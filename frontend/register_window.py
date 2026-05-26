from PySide6.QtWidgets import QDialog, QLineEdit, QMessageBox, QPushButton, QVBoxLayout
from network import NetworkThread


class RegisterWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Register")
        self.setGeometry(300, 300, 320, 220)
        self._threads = []

        layout = QVBoxLayout()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        layout.addWidget(self.username_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email")
        layout.addWidget(self.email_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_edit)

        self.register_btn = QPushButton("Register")
        self.register_btn.clicked.connect(self.register)
        layout.addWidget(self.register_btn)
        self.setLayout(layout)

    def _start_thread(self, thread):
        self._threads.append(thread)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        thread.start()

    def register(self):
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        if not username or not email or not password:
            QMessageBox.warning(self, "Warning", "Fill in all fields")
            return

        self.register_btn.setEnabled(False)
        payload = {"username": username, "email": email, "password": password}
        thread = NetworkThread("/auth/register", method="POST", json=payload)
        thread.result.connect(self.on_success)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda: self.register_btn.setEnabled(True))
        self._start_thread(thread)

    def on_success(self, data):
        QMessageBox.information(self, "Success", f"User created: {data['username']}")
        self.accept()

    def on_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
