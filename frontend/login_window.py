from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout
from network import NetworkThread


class LoginWindow(QDialog):
    login_successful = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(300, 300, 320, 230)
        self._threads = []

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Personal Finance Manager"))

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password)

        self.btn = QPushButton("Login")
        self.btn.clicked.connect(self.login)
        layout.addWidget(self.btn)

        self.register_btn = QPushButton("Register")
        self.register_btn.clicked.connect(self.open_register)
        layout.addWidget(self.register_btn)

        self.setLayout(layout)
        self.token = None
        self.requires_2fa = False
        self._login_ok = False

    def _start_thread(self, thread):
        self._threads.append(thread)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        thread.start()

    def open_register(self):
        from register_window import RegisterWindow
        dlg = RegisterWindow()
        dlg.exec()

    def login(self):
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Warning", "Enter username and password")
            return

        self.btn.setEnabled(False)
        data = {"username": username, "password": password}
        thread = NetworkThread("/auth/login", method="POST", json=data)
        thread.result.connect(self.success)
        thread.error.connect(self.error)
        thread.finished.connect(self.finish_login)
        self._start_thread(thread)

    def success(self, data):
        self.token = data.get("access_token")
        self.requires_2fa = data.get("requires_2fa", False)
        self._login_ok = bool(self.token)

    def finish_login(self):
        self.btn.setEnabled(True)
        if self._login_ok:
            self.login_successful.emit(self.token, self.requires_2fa)
            self.accept()

    def error(self, msg):
        self._login_ok = False
        QMessageBox.critical(self, "Error", msg)
