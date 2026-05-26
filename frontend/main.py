import sys
from PySide6.QtWidgets import QApplication

from login_window import LoginWindow
from two_factor_window import TwoFactorWindow
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    login = LoginWindow()
    if login.exec() == LoginWindow.DialogCode.Accepted:
        token = login.token
        if login.requires_2fa:
            twofa = TwoFactorWindow(token)
            if twofa.exec() == TwoFactorWindow.DialogCode.Accepted:
                token = twofa.final_token
            else:
                sys.exit(0)

        window = MainWindow(token)
        window.show()
        sys.exit(app.exec())

    sys.exit(0)


if __name__ == "__main__":
    main()
