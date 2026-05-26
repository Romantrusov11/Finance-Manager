from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout
from network import NetworkThread


class TwoFactorWindow(QDialog):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.final_token = None
        self._threads = []
        self.setWindowTitle("2FA")
        self.setGeometry(300, 300, 320, 160)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter 2FA code from authenticator:"))
        self.code = QLineEdit()
        self.code.setPlaceholderText("6-digit code")
        layout.addWidget(self.code)

        self.btn = QPushButton("Verify")
        self.btn.clicked.connect(self.verify)
        layout.addWidget(self.btn)
        self.setLayout(layout)

    def _start_thread(self, thread):
        self._threads.append(thread)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        thread.start()

    def verify(self):
        code = self.code.text().strip()
        if not code:
            QMessageBox.warning(self, "Warning", "Enter code")
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"code": code}
        self.btn.setEnabled(False)
        thread = NetworkThread("/auth/verify-2fa", method="POST", json=data, headers=headers)
        thread.result.connect(self.success)
        thread.error.connect(self.error)
        thread.finished.connect(lambda: self.btn.setEnabled(True))
        self._start_thread(thread)

    def success(self, data):
        self.final_token = data.get("access_token")
        if self.final_token:
            self.accept()

    def error(self, msg):
        QMessageBox.critical(self, "Error", msg)
