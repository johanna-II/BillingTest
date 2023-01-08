import libs.SessionHandler as sessionHandler
import config.url as url


class Payments:
    def __init__(self, month):
        self.month = month
        self._uuid = ""
        self._projectId = ""

    def __repr__(self):
        return f'Payments(uuid: {self.uuid}, month: {self.month}, projectId: {self.projectId})'

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        self._uuid = uuid

    @property
    def projectId(self):
        return self._projectId

    @projectId.setter
    def projectId(self, projectId):
        self._projectId = projectId

    # 청구서 목록으로 조회 (Admin에서 조회)
    def inquiryPaymentAdmin(self):
        # GET BILLING_CONSOLE_URL + /payments/ + "2020-12" + /statements" // 상태 조회
        stats_url = f"{url.BILLING_ADMIN_URL}/payments?page=1&itemsPerPage=10&monthFrom={self.month}&monthTo={self.month}&uuid={self.uuid}"
        headers = {
            "Accept": "application/json"
        }

        session = sessionHandler.SendDataSession("GET", stats_url)
        session.headers = headers
        session.retry_count = 30
        response = session.request().json()

        if response['header']['isSuccessful'] and response['statements']:
            print(f"++ 결제 상태 조회 \n {response['statements']}")

            # 통합결제가 아닌 경우 고려
            # d = {status['paymentGroupId']: status['paymentStatusCode'] for status in resp['statements']}
            print(response['statements'][0]['paymentGroupId'], response['statements'][0]['paymentStatusCode'])
            return response['statements'][0]['paymentGroupId'], response['statements'][0]['paymentStatusCode']
        else:
            print("++ 결제 상태 조회에 실패하였습니다. 임시로 empty return.")
            print(response)
            return "", ""

    # 결제 상태 조회 (콘솔 조회)
    def inquiryPayment(self):
        # stats_url = url.BILLING_CONSOLE_URL + f"/payments/{self.month}/statements?refundAccountRegisterStatusCode=DENY&page=1&itemsPerPage=100"
        stats_url = f"{url.BILLING_CONSOLE_URL}/payments/{self.month}/statements"
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "lang": "kr",
            "uuid": self.uuid
        }
        session = sessionHandler.SendDataSession("GET", stats_url)
        session.headers = headers
        response = session.request()
        json_res = response.json()

        if json_res['header']['isSuccessful'] and json_res['statements']:
            print(f"++ 결제 상태 조회가 완료되었습니다.")
            # 통합결제가 아닌 경우 고려
            # d = {status['paymentGroupId']: status['paymentStatusCode'] for status in resp['statements']}
            print(json_res['statements'][0]['paymentGroupId'], json_res['statements'][0]['paymentStatusCode'])
            return json_res['statements'][0]['paymentGroupId'], json_res['statements'][0]['paymentStatusCode']
        else:
            print("++ 결제 상태 조회에 실패하였습니다. Skipped Inquiry.")
            print(json_res)
            return "", ""

    # 결제 상태 변경 (month, uuid 필요)
    def changePayment(self, pgId):
        change_pay_url = f"{url.BILLING_ADMIN_URL}/payments/{self.month}/status"
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json"
        }
        data = {
            "paymentGroupId": pgId
        }

        session = sessionHandler.SendDataSession("PUT", change_pay_url)
        session.headers = headers
        session.json = data
        response = session.request().json()

        if response['header']['isSuccessful']:
            print(f"++ {self.month}월 결제 상태 변경이 완료되었습니다.")
            print(session)
        else:
            print(f"++ {self.month}월 결제 상태 변경에 실패하였습니다.")
            print(response)

    # 결제 취소
    def cancelPayment(self, pgId):
        delete_pay_url = f"{url.BILLING_ADMIN_URL}/payments/{self.month}?paymentGroupId={pgId}"
        headers = {
            "Accept": "application/json;charset=UTF-8"
        }
        session = sessionHandler.SendDataSession("DELETE", delete_pay_url)
        session.headers = headers
        response = session.request().json()

        if response['header']['isSuccessful']:
            print(f"++ {self.month}월 결제 취소")
            print(response)
        else:
            print(f"++ {self.month}월 결제 취소 실패하였습니다.")
            print(response['header'])

    # 즉시 결제
    def payment(self, pgId):
        payment_url = f"{url.BILLING_CONSOLE_URL}/payments/{self.month}"
        headers = {
            "Accept": "application/json;charset=UTF-8",
            "uuid": self.uuid
        }
        data = {
            "paymentGroupId": pgId
        }
        session = sessionHandler.SendDataSession("POST", payment_url)
        session.headers = headers
        session.json = data
        response = session.request().json()

        if response['header']['isSuccessful']:
            print(f"++ {self.month}월 즉시 결제가 완료되었습니다.")
            print(session)
        else:
            print(f"++ {self.month}월 즉시 결제에 실패하였습니다. 재시도 합니다.")
            print(response)
            self.payment(pgId=pgId)

    # 미납 체크
    def unpaid(self):
        unpaid_url = f"{url.BILLING_CONSOLE_URL}/payments/{self.month}/statements/unpaid"
        headers = {
            "Accept": "application/json",
            "lang": "kr",
            "uuid": self.uuid
        }
        session = sessionHandler.SendDataSession("GET", unpaid_url)
        session.headers = headers
        response = session.request().json()

        if response['header']['isSuccessful'] and response['statements']:
            print(f"++ {self.month}월의 미납 상태 조회")
            # 통합결제가 아닌 경우 고려
            # d = {status['paymentGroupId']: status['paymentStatusCode'] for status in resp['statements']}
            return response['statements'][0]['totalAmount']
        else:
            print("++ 청구서를 찾을 수 없습니다. 아래 응답을 체크해주세요. ")
            print(response)
            return 0
