from collections import defaultdict

import libs.SessionHandler as sessionHandler
import config.url as url


class Contract:
    def __init__(self, month, bgId):
        self.month = month
        self.bgId = bgId
        self._contractId = ""
        self._counterName = ""

    def __repr__(self):
        print(f"Contract(bgId: {self.bgId}, contractId: {self.contractId}, "
              f"month: {self.month}, counterName: {self.counterName})")

    @property
    def contractId(self):
        return self._contractId

    @contractId.setter
    def contractId(self, contractId):
        self._contractId = contractId

    @property
    def counterName(self):
        return self._counterName

    @counterName.setter
    def counterName(self, counterName):
        self._counterName = counterName

    # 약정 등록
    def applyContract(self):
        bg_contract_req_url = f'{url.BILLING_ADMIN_URL}/billing-groups/{self.bgId}'
        session = sessionHandler.SendDataSession("PUT", bg_contract_req_url)
        session.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        session.json = {
            "contractId": self.contractId,
            "defaultYn": "Y",
            "monthFrom": self.month,
            "name": "billing group default"
        }
        print(f"{self.month}월을 시작으로 약정 요금제를 시작합니다. 약정요금제: {self.contractId}")
        response = session.request().json()
        if response["header"]["isSuccessful"]:
            print("+ 약정 요금제 신청 완료")
        else:
            print("약정 요금제 신청에 실패하였습니다. 아래 메시지 확인해주세요.")
            print(response)

    # 약정 삭제
    def deleteContract(self):
        bg_contract_req_url = f'{url.BILLING_ADMIN_URL}/billing-groups/{self.bgId}/contracts'
        session = sessionHandler.SendDataSession("DELETE", bg_contract_req_url)
        session.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        print(f"{self.month}월 약정 요금제를 삭제 처리합니다. ")
        response = session.request().json()
        if response["header"]["isSuccessful"]:
            print("+ 약정 요금제 삭제 완료")
        else:
            print("약정 요금제 삭제 실패하였습니다. 아래 메시지 확인해주세요.")
            print(response)

    # 약정 상품 조회
    def inquiryContract(self):
        req_url = f'{url.BILLING_ADMIN_URL}/contracts/{self.contractId}'
        session = sessionHandler.SendDataSession("GET", req_url)
        session.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"

        }
        print(f"+ 약정 요금제를 조회합니다. 약정요금제: {self.contractId}")
        response = session.request().json()
        if response["header"]["isSuccessful"]:
            print("+ 약정 요금제 조회 완료")
            print(response['contract']['baseFee'])
        else:
            print("약정 요금제 신청에 실패하였습니다. 아래 메시지 확인해주세요.")
            print(response)

    # 약정에 등록된 카운터네임의 가격 조회
    def inquiryPricebyCounterName(self):
        req_url = f'{url.BILLING_ADMIN_URL}/contracts/{self.contractId}/products/prices?counterNames={self.counterName}'
        session = sessionHandler.SendDataSession("GET", req_url)
        session.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"

        }
        print(f"+ 약정 요금제를 조회합니다. 약정요금제: {self.contractId}")

        while True:
            response = session.request().json()
            if response["header"]["isSuccessful"]:
                print(f"+ {self.counterName}이 속한 약정 요금제 가격 조회 완료")
                cntcont = defaultdict(set)
                cntcont['price'].add(response['prices']['price'])
                cntcont['originalPrice'].add(response['prices']['originalPrice'])
                print('할인된 금액: ', response['prices']['price'], '원래 금액: ', response['prices']['originalPrice'])
                return cntcont
            else:
                print("약정 요금제 신청에 실패하였습니다. 아래 메시지 확인해주세요.")
                print(response)
                continue
