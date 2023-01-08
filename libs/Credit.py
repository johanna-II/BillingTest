import config.url as url
import libs.SessionHandler as sessionHandler


class Credit:
    def __init__(self):
        self._couponcode = ""
        self._uuid = ""
        self._headers = ""
        self._campaign_id = []
        self._give_campaign_id = []
        self._paid_campaign_id = []

    def __repr__(self):
        return f'Credit(couponCode: {self.couponcode}, ' \
               f'uuid: {self.uuid}, couponId: {self.campaign_id}, giveCouponId: {self.give_campaign_id}, paidCampaignId: {self.paid_campaign_id}'

    @property
    def couponcode(self):
        return self._couponcode

    @couponcode.setter
    def couponcode(self, couponcode):
        self._couponcode = couponcode

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        self._uuid = uuid

    @property
    def campaign_id(self):
        return self._campaign_id

    @campaign_id.setter
    def campaign_id(self, campaign_id):
        self._campaign_id = campaign_id

    @property
    def give_campaign_id(self):
        return self._give_campaign_id

    @give_campaign_id.setter
    def give_campaign_id(self, give_campaign_id):
        self._give_campaign_id = give_campaign_id

    @property
    def paid_campaign_id(self):
        return self._paid_campaign_id

    @paid_campaign_id.setter
    def paid_campaign_id(self, paid_campaign_id):
        self._paid_campaign_id = paid_campaign_id

    # kwargs -> 지급형 / 없으면 쿠폰형
    def giveCredit(self, couponCode, *args):
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "uuid": self.uuid
        }

        if args:
            credit_url = f"{url.CREDIT_GIVE_URL + couponCode}/credits"
            data = {
                "creditName": "QA billing test",
                "credit": args[0],
                "expirationDateFrom": None,
                "expirationDateTo": None,
                "expirationPeriod": 1,
                "creditPayTargetData": self.uuid,
                "emailList": [],
                "uuidList": [self.uuid]
            }
            session = sessionHandler.SendDataSession("POST", credit_url)
            session.headers = headers
            session.json = data
            print(f'지급형 크레딧을 지급 요청합니다. 쿠폰코드: {couponCode}, 요청금액: {args[0]}')
        else:
            credit_url = url.CREDIT_COUPON_URL + couponCode
            session = sessionHandler.SendDataSession("POST", credit_url)
            session.headers = headers
            print(f'쿠폰형 크레딧을 지급 요청합니다. 쿠폰코드: {couponCode}')

        response = session.request().json()
        if response['header']['isSuccessful']:
            print("++ 크레딧 지급 완료, ", response)
        else:
            print("++ 크레딧 지급 실패, 아래 응답 메시지를 확인해주세요. ")
            print(response)

    def givePaidCredit(self, **kwargs):
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "Content-Type": "application/json",
            "uuid": self.uuid
        }
        for k, v in kwargs.items():
            globals()[f'{k}'] = v

        credit_url = f'{url.CREDIT_GIVE_URL + campaignId}/credits'
        session = sessionHandler.SendDataSession("POST", credit_url)
        session.headers = headers
        session.json = {
            "credit": creditAmount,
            "creditName": "test",
            "expirationDateFrom": "2021-03-01",
            "expirationDateTo": "2022-03-01",
            "expirationPeriod": 1,
            "uuidList": [
                self.uuid
            ]
        }
        print(f'유료 크레딧을 지급 요청합니다. 크레딧 ID: {campaignId} 크레딧 금액: {creditAmount}')

        response = session.request().json()
        if response['header']['isSuccessful']:
            print("++ 크레딧 지급 완료, ", response)
        else:
            print("++ 크레딧 지급 실패, 아래 응답 메시지를 확인해주세요. ")
            print(response)

    # 크레딧 내역 조회 시 파라미터 (FREE/PAID)
    def inquiryCredit(self, *args):
        credit_history_url = f"{url.CREDIT_HISTORY_URL}?balancePriceTypeCode={args[0]}&page=1&itemsPerPage=100"
        headers = {
            "Accept": "application/json;charset=UTF-8",
            'uuid': self.uuid
        }

        session = sessionHandler.SendDataSession("GET", credit_history_url)
        session.headers = headers
        response = session.request().json()

        if response['header']['isSuccessful']:
            print("+ 크레딧 내역 조회 성공")
            return response['totalCreditAmt']
        else:
            print("++ 크레딧 내역 조회에 실패하였습니다. 아래 응답을 참고하세요.")
            print(response)
            return

    # 남은 크레딧 조회
    def inquiryRestCredit(self):
        rest_credit = f"{url.BILLING_CONSOLE_V5}/credits"
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "uuid": self.uuid
        }

        credit_session = sessionHandler.SendDataSession("GET", rest_credit)
        credit_session.headers = headers
        credit_response = credit_session.request().json()

        free_credit_history = int(self.inquiryCredit('FREE'))
        paid_credit_history = int(self.inquiryCredit('PAID'))

        if credit_response['header']['isSuccessful']:
            print("++ 남은 크레딧 조회")
            if not credit_response['stats']['totalAmount'] == 0:
                print("잔여 크레딧이 존재합니다. 아래 내용을 참고해주세요.")
                for arr in credit_response['stats']['restCreditsByBalancePriceTypeCode']:
                    free_rest_credit = arr['restAmount'] if arr['balancePriceTypeCode'] == 'FREE' else 0
                    paid_rest_credit = arr['restAmount'] if arr['balancePriceTypeCode'] == 'PAID' else 0
                    print(f"++ 무료 잔여 크레딧: {free_rest_credit}, 유료 잔여 크레딧: {paid_rest_credit}")
            else:
                print("잔여 크레딧을 모두 소진하였습니다.")
            totalCreditAmt = free_credit_history + paid_credit_history
            print(f'++ 무/유료 통합 잔여 크레딧: {totalCreditAmt}', credit_response['stats']['totalAmount'])
            return credit_response['stats']['totalAmount'], totalCreditAmt
        else:
            print("크레딧 내역 조회에 실패하였습니다.")
            print(credit_response['header'])
            return "", ""

    # 크레딧 적립 취소
    def cancelCredit(self):
        headers = {
            "Accept": "application/json;charset=UTF-8"
        }

        # coupon_all = itertools.chain.from_iterable({**self.campaign_id, **self.give_campaign_id}.values())
        # coupon_all = itertools.chain.from_iterable(self.campaign_id + self.give_campaign_id)
        coupon_all = self.campaign_id + self.give_campaign_id + self.paid_campaign_id
        for coupon_id in coupon_all:
            cancel_credit = f"{url.BILLING_ADMIN_URL}/campaign/{coupon_id}/credits?reason=test"

            credit_session = sessionHandler.SendDataSession("DELETE", cancel_credit)
            credit_session.headers = headers
            credits_resp = credit_session.request().json()

            if credits_resp['header']['isSuccessful']:
                print(f"++ 크레딧 {coupon_id} 적립 취소가 완료되었습니다. ")

            else:
                print("++ 크레딧 적립 취소가 실패했습니다.")
                print(f"++++ 크레딧: {coupon_id} \n ", credits_resp['header'])
