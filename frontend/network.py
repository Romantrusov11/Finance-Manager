import requests
from PySide6.QtCore import QThread, Signal

BASE_URL = "http://127.0.0.1:8000"


class NetworkThread(QThread):
    result = Signal(object)
    error = Signal(str)

    def __init__(self, endpoint, method="GET", json=None, headers=None):
        super().__init__()
        self.url = BASE_URL + endpoint
        self.method = method.upper()
        self.json = json
        self.headers = headers or {}

    def run(self):
        try:
            if self.method == "GET":
                response = requests.get(self.url, headers=self.headers, timeout=10)
            elif self.method == "POST":
                response = requests.post(self.url, json=self.json, headers=self.headers, timeout=10)
            elif self.method == "PUT":
                response = requests.put(self.url, json=self.json, headers=self.headers, timeout=10)
            elif self.method == "DELETE":
                response = requests.delete(self.url, headers=self.headers, timeout=10)
            else:
                self.error.emit("Unsupported HTTP method")
                return

            response.raise_for_status()
            try:
                self.result.emit(response.json())
            except Exception:
                self.result.emit({"message": response.text})
        except Exception as error:
            self.error.emit(str(error))
