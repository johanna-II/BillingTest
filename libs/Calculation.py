import time
import config.url as url
import libs.SessionHandler as sessionHandler


class Calculation:
    def __init__(self, month, uuid):
        self.month = month
        self.uuid = uuid

    def __repr__(self):
        return f'Calculation(month: {self.month}, uuid: {self.uuid})'

    def recalculationAll(self):
        calc_url = url.BILLING_ADMIN_URL + "/calculations"
        data = {
            'includeUsage': True,
            'month': self.month,
            'uuid': self.uuid
        }
        session = sessionHandler.SendDataSession("POST", calc_url)
        session.json = data
        response = session.request().json()

        if response['header']['isSuccessful']:
            print(f"uuid: {self.uuid}에 대한 {self.month}월 전체 재정산 요청이 완료되었습니다. 정산 진행율을 체크합니다.")
            self.checkStable()
        else:
            print("정산이 진행되지 못했습니다. 아래 응답을 참고하세요. ")
            print(response)

    def checkStable(self):
        flag = False

        print(f"uuid: {self.uuid}에 대한 {self.month} 정산 진행율을 체크합니다.")
        while not flag:
            progress_url = url.BILLING_ADMIN_URL + "/progress"
            session = sessionHandler.SendDataSession("GET", progress_url)
            time.sleep(3)
            response = session.request().json()
            for item in response['progressStatusList']:
                if item['progressCode'] == 'API_CALCULATE_USAGE_AND_PRICE':
                    if item['progress'] == item['maxProgress']:
                        print('일치', item['progressCode'], item['progress'], item['maxProgress'])
                        flag = True

    def deleteResources(self):
        del_res_url = url.BILLING_ADMIN_URL + f"/resources?month={self.month}"
        headers = {
            'uuid': self.uuid
        }
        session = sessionHandler.SendDataSession("DELETE", del_res_url)
        session.headers = headers
        # retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[12007, 31000])
        # session.mount(del_res_url, HTTPAdapter(max_retries=retries))
        response = session.request().json()

        if response['header']['isSuccessful']:
            print(f"{self.month}월의 정산 리소스 삭제 완료")
        else:
            print("정산 리소스가 삭제되지 않았습니다. 아래 응답을 참고하세요. ")
            print(response)
