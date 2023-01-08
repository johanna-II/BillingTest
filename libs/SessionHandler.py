from requests import Session


class SendDataSession(Session):
    def __init__(self, method, url):
        super().__init__()
        self.method = method
        self.url = url
        self._data = ""
        self._json = {}
        self._headers = {}
        self.request_session = Session()

    def __repr__(self):
        return f'Session(method: {self.method}, requestUrl: {self.url}, ' \
               f'data: {self.data}, json: {self.json}, headers: {self.headers})'

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    @property
    def json(self):
        return self._json

    @json.setter
    def json(self, json):
        self._json = json

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        self._headers = headers

    def request(self, **kwargs):
        return self.request_session.request(self.method, self.url,
                                            data=self.data if self.data else None,
                                            json=self.json if self.json else None,
                                            headers=self.headers if self.headers else None)
