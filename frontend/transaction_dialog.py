from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class TransactionDialog(QDialog):
    def __init__(self, parent=None, title="Add Transaction", transaction=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(350, 350, 360, 260)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Amount"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMaximum(1_000_000_000)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.amount_spin)

        layout.addWidget(QLabel("Category"))
        self.category_edit = QLineEdit()
        layout.addWidget(self.category_edit)

        layout.addWidget(QLabel("Description"))
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(70)
        layout.addWidget(self.description_edit)

        buttons = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self.ok_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)
        self.setLayout(layout)

        if transaction:
            self.amount_spin.setValue(float(transaction.get("amount", 0)))
            self.category_edit.setText(transaction.get("category", ""))
            self.description_edit.setPlainText(transaction.get("description") or "")

    def get_data(self):
        return {
            "amount": float(self.amount_spin.value()),
            "category": self.category_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
        }
