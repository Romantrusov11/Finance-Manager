import base64
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout
from network import NetworkThread


class Setup2FAWindow(QDialog):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.secret = None
        self._threads = []
        self.setWindowTitle("Setup 2FA")
        self.setGeometry(300, 300, 420, 500)

        layout = QVBoxLayout()
        self.qr = QLabel()
        self.qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.qr)

        self.secret_label = QLabel()
        layout.addWidget(self.secret_label)

        self.code = QLineEdit()
        self.code.setPlaceholderText("Enter code")
        layout.addWidget(self.code)

        self.btn = QPushButton("Enable 2FA")
        self.btn.clicked.connect(self.enable)
        layout.addWidget(self.btn)

        self.setLayout(layout)
        self.load_qr()

    def _start_thread(self, thread):
        self._threads.append(thread)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        thread.start()

    def load_qr(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        thread = NetworkThread("/auth/setup-2fa", headers=headers)
        thread.result.connect(self.show_qr)
        thread.error.connect(self.error)
        self._start_thread(thread)

    def show_qr(self, data):
        self.secret = data.get("secret")
        self.secret_label.setText(f"Secret: {self.secret}")
        qr_base64 = data.get("qr_url", "")
        try:
            if qr_base64.startswith("data:image/png;base64,"):
                qr_base64 = qr_base64.split(",", 1)[1]
            pixmap = QPixmap()
            ok = pixmap.loadFromData(base64.b64decode(qr_base64))
            if ok:
                self.qr.setPixmap(pixmap.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                self.qr.setText("QR code loading error")
        except Exception:
            self.qr.setText("QR code loading error")

    def enable(self):
        code = self.code.text().strip()
        if not code:
            QMessageBox.warning(self, "Warning", "Enter code")
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"code": code, "secret": self.secret}
        self.btn.setEnabled(False)
        thread = NetworkThread("/auth/enable-2fa", method="POST", json=data, headers=headers)
        thread.result.connect(self.success)
        thread.error.connect(self.error)
        thread.finished.connect(lambda: self.btn.setEnabled(True))
        self._start_thread(thread)

    def success(self, data):
        QMessageBox.information(self, "Success", "2FA enabled successfully")
        self.accept()

    def error(self, msg):
        QMessageBox.critical(self, "Error", msg)
