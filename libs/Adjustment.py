import libs.SessionHandler as sessionHandler
import config.url as url


class Adjustments:
    def __init__(self, month):
        self.month = month

    def __repr__(self):
        return f'Adjustments({self.month})'

    # 할인/할증 등록
    def applyAdjustment(self, **kwargs):
        for k, v in kwargs.items():
            globals()[f'{k}'] = v

        json = {
            "adjustment": adjustment,
            "adjustmentTypeCode": adjustmentType,
            "descriptions": [
                {
                    "locale": "ko",
                    "message": "QA billing automation test"
                }
            ],
            "monthFrom": self.month,
            "monthTo": self.month
        }

        if adjustmentTarget == "BillingGroup":
            adj_req_url = f'{url.BILLING_ADMIN_URL}/billing-groups/adjustments'
            json['billingGroupId'] = billingGroupId
        else:
            adj_req_url = f'{url.BILLING_ADMIN_URL}/projects/adjustments'
            json['projectId'] = projectId

        session = sessionHandler.SendDataSession("POST", adj_req_url)
        session.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        session.json = json
        print(f"{self.month}월 프로젝트 혹은 빌링그룹의 할인/할증을 설정합니다. ")
        print(f"할인타입: {adjustmentType}, 할인금액/퍼센트: {adjustment}")
        response = session.request().json()

        if response["header"]["isSuccessful"]:
            print("+ 프로젝트 혹은 빌링 그룹의 할인/할증 설정 완료")
        else:
            print("할인/할증 등록에 실패하였습니다. 아래 메시지 확인해주세요.")
            print(response)

    def inquiryAdjustment(self, **kwargs):
        for k, v in kwargs.items():
            globals()[f'{k}'] = v

        if adjustmentTarget == "BillingGroup":
            adj_req_url = f'{url.BILLING_ADMIN_URL}/billing-groups/adjustments?page=1&itemsPerPage=50&billingGroupId={billingGroupid}'
        else:
            adj_req_url = f'{url.BILLING_ADMIN_URL}/projects/adjustments?page=1&itemsPerPage=50&projectId={projectId}'

        session = sessionHandler.SendDataSession("GET", adj_req_url)
        session.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        print(f"{self.month}월 프로젝트 혹은 빌링그룹의 할인/할증 ID를 조회합니다. ")
        response = session.request().json()
        adjIdlist = []

        if response["header"]["isSuccessful"]:
            print("+ 프로젝트 혹은 빌링 그룹의 할인/할증 ID 조회 완료")
            for item in response['adjustments']:
                adjIdlist.append(item['adjustmentId'])
            print('++ 프로젝트 혹은 빌링그룹 AdjustmentId 리스트 ', adjIdlist)
            return adjIdlist
        else:
            print("할인/할증 ID 조회에 실패하였습니다. 아래 메시지 확인해주세요.")
            print(response)
            return None

    def deleteAdjustment(self, adjIdList):
        for item in adjIdList:
            if adjustmentTarget == "BillingGroup":
                adj_req_url = f'{url.BILLING_ADMIN_URL}/billing-groups/adjustments?adjustmentIds={item}'
            else:
                adj_req_url = f'{url.BILLING_ADMIN_URL}/projects/adjustments?adjustmentIds={item}'

            session = sessionHandler.SendDataSession("DELETE", adj_req_url)
            session.headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            print(f"{self.month}월 프로젝트 혹은 빌링그룹의 할인/할증을 삭제합니다. ")
            response = session.request().json()

            if response["header"]["isSuccessful"]:
                print("+ 프로젝트 혹은 빌링 그룹의 할인/할증 삭제 완료")
            else:
                print("할인/할증 ID 조회에 실패하였습니다. 아래 메시지 확인해주세요.")
                print(response)