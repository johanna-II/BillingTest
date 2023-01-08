import libs.SessionHandler as sessionHandler
import config.url as url


class Batches:
    def __init__(self, month):
        self.month = month
        self._batchJobCode = ""

    def __repr__(self):
        return f'Batches(month: {self.month}, batchJobCode: {self.batchJobCode})'

    @property
    def batchJobCode(self):
        return self._batchJobCode

    @batchJobCode.setter
    def batchJobCode(self, batchJobCode):
        self._batchJobCode = batchJobCode

    def sendBatchRequest(self):
        batch_url = url.BILLING_ADMIN_URL + "/batches"
        session = sessionHandler.SendDataSession("POST", batch_url)
        session.headers = {
            "Accept": "application/json",
            "lang": "kr"
        }
        session.json = {
            'async': 'true',
            'batchJobCode': self.batchJobCode,
            'date': self.month + "-15T00:00:00+09:00"
        }
        print(f'{self.month}월 기준으로 배치를 요청합니다. batchJobCode: {self.batchJobCode}')
        response = session.request().json()
        if response['header']['isSuccessful']:
            print("+ 배치 요청 완료")
        else:
            print("배치 요청이 진행되지 않았습니다. 아래 응답을 참고하세요.")
            print(response)
