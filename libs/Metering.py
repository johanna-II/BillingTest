from datetime import date
from dateutil.utils import today
import libs.SessionHandler as sessionHandler
import calendar
import config.url as url


class Metering:
    def __init__(self, month):
        self.month = month
        self._appkey = ""
        self._iaas_template = {
            "meterList": [
                {
                    "appKey": "",
                    "counterName": "",
                    "counterType": "",
                    "counterUnit": "",
                    "counterVolume": "",
                    "parentResourceId": "test",
                    "resourceId": "test",
                    "resourceName": "test",
                    "source": "qa.billing.test",
                    "timestamp": ""
                }
            ]
        }

    def __repr__(self):
        return f'Metering(month: {self.month}, appkey: {self.appkey}, iaas_template: {self._iaas_template})'

    @property
    def appkey(self):
        return self._appkey

    @appkey.setter
    def appkey(self, appkey):
        self._appkey = appkey

    def deleteMetering(self):
        year, month = str(self.month).split("-")
        _, nDaysofMonth = calendar.monthrange(int(year), int(month))
        fromDate = str(self.month + "-" + "01")
        toDate = str(self.month + "-" + str(nDaysofMonth))

        for appkey in self.appkey:
            del_meter_url = url.METERING_ADMIN_URL + "/meters?appKey=" + appkey + "&from=" + fromDate + "&to=" + toDate
            session = sessionHandler.SendDataSession("DELETE", del_meter_url)
            session.json = self._iaas_template
            response = session.request().json()
            if response['header']['isSuccessful']:
                print(f"{self.month}월의 미터링 삭제 완료")
            else:
                print("미터링 삭제 처리가 되지 않았습니다. 아래 응답을 참고하세요.")
                print(response)

    def sendIaaSMetering(self, **kwargs):
        self._iaas_template['meterList'][0].update({'appKey': f'{self.appkey}'})
        for key, value in kwargs.items():
            self._iaas_template['meterList'][0].update({f'{key}': f'{value}'})
        self._iaas_template['meterList'][0].update({'timestamp': self.month + "-01T13:00:00.000+09:00"})

        session = sessionHandler.SendDataSession("POST", url.METERING_URL)
        session.json = self._iaas_template
        response = session.request().json()
        if response['header']['isSuccessful']:
            print(f"{self.month}월 미터링 전송 완료")
        else:
            print(f"{self.month}월 미터링 전송에 실패하였습니다. 아래 응답메시지를 확인해주세요.")
            print(response)
