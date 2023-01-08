from bs4 import BeautifulSoup as bs
import urllib.request as url_req
import config.url as url
import libs.SessionHandler as sessionHandler
import libs.Metering as metering
import config.alpha_kr as alpha_kr
import config.alpha_etc as alpha_etc
import libs.Credit as credit
import libs.Payments as pmts
import libs.Calculation as calc
import libs.Contract as contract
import libs.Adjustment as adj


class InitializeConfig:
    def __init__(self, env, member, month):
        self.uuid = globals()[f"{env}_{member}"].config["uuid"]
        self.billing_group_id = globals()[f"{env}_{member}"].config["billing_group_id"]
        self.project_id = globals()[f"{env}_{member}"].config["project_id"]
        self.appkey = globals()[f"{env}_{member}"].config["appkey"]
        self.campaign_id = globals()[f"{env}_{member}"].config["campaign_id"]
        self.give_campaign_id = globals()[f"{env}_{member}"].config["give_campaign_id"]
        self.paid_campaign_id = globals()[f"{env}_{member}"].config["paid_campaign_id"]
        self.month = month
        self.member = member

    def beforeTest(self):
        paymentsObj = pmts.Payments(self.month)
        paymentsObj.uuid = self.uuid
        pgId, pgStatusCode = paymentsObj.inquiryPayment()  # can got paymentGroupId, paymentStatus
        if pgStatusCode == "PAID":  # 결제 완료 상태인 경우
            paymentsObj.cancelPayment(pgId)  # 결제 취소
            paymentsObj.changePayment(pgId)  # READY -> REGISTERED로 변경
        elif pgStatusCode == "READY":
            paymentsObj.changePayment(pgId)  # READY -> REGISTERED로 변경
        else:
            print('Payment status is REGISTERED. so skipped change')

    def cleanData(self):
        self.cleanMetering()
        self.cleanContract()
        self.cleanAdjustment()
        self.cleanCalculation()

    def cleanAdjustment(self):
        adjObj = adj.Adjustments(self.month)
        adjlist = adjObj.inquiryAdjustment(adjustmentTarget="Project", projectId=self.project_id[0])
        if adjlist:
            adjObj.deleteAdjustment(adjlist)
        adjlist = adjObj.inquiryAdjustment(adjustmentTarget="BillingGroup", billingGroupid=self.billing_group_id[0])
        if adjlist:
            adjObj.deleteAdjustment(adjlist)

    def cleanCalculation(self):
        calcObj = calc.Calculation(self.month, self.uuid)
        calcObj.deleteResources()
        # calcObj.recalculationAll()

    def cleanContract(self):
        contractObj = contract.Contract(self.month, self.billing_group_id[0])
        contractObj.deleteContract()

    def cleanMetering(self):
        meteringObj = metering.Metering(self.month)
        meteringObj.appkey = self.appkey
        meteringObj.deleteMetering()

    # usage 조회 (프로젝트)
    def inquiryProjectUsageExceptCredit(self):
        usage = url.BILLING_CONSOLE_URL + f"/payments/{self.month}/statements"
        headers = {
            "uuid": self.uuid,
            "lang": "kr"
        }

        session = sessionHandler.SendDataSession("GET", usage)
        session.headers = headers
        response = session.request().json()

        if response['header']['isSuccessful']:
            totalAmount = response['statements'][0]['totalAmount']
            charge = response['statements'][0]['charge']
            taxAmount = response['statements'][0]['taxAmount']

            print("++ 프로젝트 이용 현황 조회")

            print("총 사용 금액: ", charge)
            print("부가세 (10%): ", taxAmount)
            print("부가세 포함 총 결제 요청 금액: ", totalAmount)
            return totalAmount
        else:
            print("++ 프로젝트 이용 현황 조회에 실패하였습니다. 아래 코드를 살펴봐 주세요.")
            print(response['header'])

    # usage 조회 (프로젝트)
    def inquiryProjectUsage(self):
        usage = url.BILLING_CONSOLE_URL + f"/payments/{self.month}/statements"
        headers = {
            "uuid": self.uuid,
            "lang": "kr"
        }

        session = sessionHandler.SendDataSession("GET", usage)
        session.headers = headers
        response = session.request().json()

        freeCreditLimit = freeCreditAll = paidCreditAll = paidCreditLimit = 0

        if response['header']['isSuccessful']:
            for item in response['statements']:
                freeCreditLimit = item['freeCreditLimit']
                freeCreditAll = item['freeCreditAll']
                paidCreditLimit = item['paidCreditLimit']
                paidCreditAll = item['paidCreditAll']
            totalAmount = response['statements'][0]['totalAmount']
            charge = response['statements'][0]['charge']
            taxAmount = response['statements'][0]['taxAmount']

            print("++ 프로젝트 이용 현황 조회")

            print("총 사용 금액: ", charge)
            print("무료 전체형 크레딧: ", freeCreditAll)
            print("무료 제한형 크레딧: ", freeCreditLimit)
            print("유료 전체형 크레딧: ", paidCreditAll)
            print("유료 제한형 크레딧: ", paidCreditLimit)
            print("부가세 (10%): ", taxAmount)
            print("부가세 포함 총 결제 요청 금액: ", totalAmount)

            return response['statements'][0]
        else:
            print("++ 프로젝트 이용 현황 조회에 실패하였습니다. 아래 코드를 살펴봐 주세요.")
            print(response['header'])

    # 매출전표 확인
    def checkSalesSlip(self, pgId):
        receipt_url = url.BILLING_CONSOLE_URL + f"/payments/{self.month}/receipt?paymentGroupId={pgId}"
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "uuid": self.uuid
        }

        session = sessionHandler.SendDataSession("GET", receipt_url)
        session.headers = headers
        response = session.request().json()

        if response['header']['isSuccessful']:  # 매출 전표가 나오는 경우
            print("++ 영수증 조회")
            print(response['url'])
            # 영수증 URL에서 form data 읽어오기
            open_resp = url_req.urlopen(response['url'])
            read_url = open_resp.read()
            soup = bs(read_url, 'html.parser')
            # dict {name: value} --> input 항목을 모두 찾아서 dict로 저장함
            d = {form_input['name']: form_input.get('value', '') for form_input in soup.find_all('input')}
            # 실제 form data를 받을 action에 해당하는 url 리턴
            act = soup.find('form').get('action')
            # submit form action
            redirect = sessionHandler.SendDataSession("POST", act)
            redirect.data = d
            redirect_resp = redirect.request()

            # 매출전표 리턴받은 후 html로 재저장해서 파싱한 후 총결제금액 nextSibling의 text를 가져온다.
            sec_soup = bs(redirect_resp.text, 'html.parser')
            total_pay_element = sec_soup.find('td', attrs={'class': 'bd_info_04 rd'})
            total_amount_element = total_pay_element.find('span', attrs={'style': 'float: right;'}).text
            total_amount = ''.join(total_amount_element.split(','))
            print("++ 매출전표에서 추출된 총 결제 금액: ", total_amount)
            return int(total_amount)
        elif response['header']['resultCode'] == 12009:
            print("크레딧으로 매출이 모두 결제되어 매출 전표가 나오지 않습니다. ")
            return 0
        else:
            print("즉시 결제에 실패하였습니다.")
            print(response['header'])
            return 0

    # 테스트 공통 호출 메소드 wrapping
    def commonTest(self):
        # change payment status & immediately pay
        paymentsObj = pmts.Payments(self.month)
        paymentsObj.uuid = self.uuid
        pgId, pgStatusCode = paymentsObj.inquiryPayment()  # can got paymentGroupId, paymentStatus
        print(paymentsObj)
        if pgStatusCode == "PAID":
            paymentsObj.cancelPayment(pgId)
            # paymentsObj.changePayment(pgId)
        elif pgStatusCode == "REGISTERED":
            paymentsObj.changePayment(pgId)
        # 변경 후
        pgId, pgStatusCode = paymentsObj.inquiryPayment()  # can got paymentGroupId, paymentStatus
        print(f'결제 상태 ID: {pgId}, StatusCode: {pgStatusCode}')
        paymentsObj.payment(pgId)
        # Assert usage & payments as using sales slip
        statements = self.inquiryProjectUsage()  # get a statement
        if self.member == "kr":
            total_payments = self.checkSalesSlip(pgId)
        else:
            total_payments = None
        return statements, total_payments

    def verifyAssert(self, **kwargs):
        for k, v in kwargs.items():
            globals()[f'{k}'] = v

        if self.member == "kr":
            print("This member from KR")
            try:
                if rest_credit:
                    assert (rest_credit == total_credit == expected_credit), f"남은 크레딧: {rest_credit}/전체 크레딧: {total_credit}와 기대 결과 값: {expected_credit}이 다릅니다."
            except NameError as ne:
                print('크레딧 케이스에 해당하지 않습니다. 크레딧 없이 사용금액, 결제금액, 기대결과와 비교합니다. ')
                assert (statements == payments == expected_result), f"결제 관리: {statements}/영수증 매출 전표: {payments}와 기대 결과 값: {expected_result}이 다릅니다."
        else:
            print("This member from JP or ETC")
            assert (statements == expected_result), f"결제 관리: {statements}와 기대 결과 값: {expected_result}이 다릅니다."

        # unpaid flag true 일 때, 즉 연체료 케이스에 해당하는 경우 assertion
        try:
            if unpaid:
                assert (prev_unpaid == current_unpaid == expect_unpaid_total), f"전전월 연체료: {prev_unpaid}, 전월 연체료: {current_unpaid}와 기대값: {expect_unpaid_total}이 다릅니다."
        except NameError as ne:
            print("연체료 케이스에 해당하지 않습니다. 연체료 비교는 Skip합니다. ")