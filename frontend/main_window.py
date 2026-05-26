from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from network import NetworkThread


class MainWindow(QMainWindow):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.setWindowTitle("Personal Finance Manager")
        self.setGeometry(100, 100, 900, 650)

        self._threads = []
        self.current_transactions = []
        self.current_report_id = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.status_label = QLabel("Logged in successfully")
        layout.addWidget(self.status_label)

        self.load_btn = QPushButton("Load Transactions")
        self.load_btn.clicked.connect(self.load_transactions)
        layout.addWidget(self.load_btn)

        self.add_btn = QPushButton("Add Transaction")
        self.add_btn.clicked.connect(self.add_transaction)
        layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Edit Selected Transaction")
        self.edit_btn.clicked.connect(self.edit_selected_transaction)
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete Selected Transaction")
        self.delete_btn.clicked.connect(self.delete_selected_transaction)
        layout.addWidget(self.delete_btn)

        self.setup_2fa_btn = QPushButton("Setup 2FA")
        self.setup_2fa_btn.clicked.connect(self.setup_2fa)
        layout.addWidget(self.setup_2fa_btn)

        self.stats_btn = QPushButton("Show Statistics")
        self.stats_btn.clicked.connect(self.show_statistics)
        layout.addWidget(self.stats_btn)

        self.charts_btn = QPushButton("Show Charts")
        self.charts_btn.clicked.connect(self.show_charts)
        layout.addWidget(self.charts_btn)

        self.generate_report_btn = QPushButton("Generate Report in Background")
        self.generate_report_btn.clicked.connect(self.generate_report)
        layout.addWidget(self.generate_report_btn)

        self.check_report_btn = QPushButton("Check Report Status")
        self.check_report_btn.clicked.connect(self.check_report_status)
        layout.addWidget(self.check_report_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Amount", "Category", "Description", "Created"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _start_thread(self, thread: NetworkThread):
        self._threads.append(thread)

        def cleanup():
            try:
                if thread in self._threads:
                    self._threads.remove(thread)
            finally:
                thread.deleteLater()

        thread.finished.connect(cleanup)
        thread.start()
        return thread

    def load_transactions(self):
        self.result_text.setText("Loading transactions...")
        thread = NetworkThread("/transactions", method="GET", headers=self.headers())
        thread.result.connect(self.on_load_result)
        thread.error.connect(self.on_error)
        self._start_thread(thread)

    def on_load_result(self, data):
        self.current_transactions = data
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("amount", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("category", "")))
            self.table.setItem(row, 3, QTableWidgetItem(item.get("description") or ""))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get("created_at", ""))))
        self.result_text.setText(f"Loaded {len(data)} transactions")

    def add_transaction(self):
        from transaction_dialog import TransactionDialog

        dlg = TransactionDialog(self, title="Add Transaction")
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        payload = dlg.get_data()
        if not payload["category"]:
            QMessageBox.warning(self, "Warning", "Category is required")
            return
        self.add_btn.setEnabled(False)
        thread = NetworkThread("/transactions", method="POST", json=payload, headers=self.headers())
        thread.result.connect(self.on_transaction_changed)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda: self.add_btn.setEnabled(True))
        self._start_thread(thread)

    def edit_selected_transaction(self):
        from transaction_dialog import TransactionDialog

        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Select a transaction first")
            return
        transaction = self.current_transactions[selected_row]
        dlg = TransactionDialog(self, title="Edit Transaction", transaction=transaction)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        payload = dlg.get_data()
        if not payload["category"]:
            QMessageBox.warning(self, "Warning", "Category is required")
            return
        transaction_id = transaction["id"]
        self.edit_btn.setEnabled(False)
        thread = NetworkThread(f"/transactions/{transaction_id}", method="PUT", json=payload, headers=self.headers())
        thread.result.connect(self.on_transaction_changed)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda: self.edit_btn.setEnabled(True))
        self._start_thread(thread)

    def delete_selected_transaction(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Select a transaction first")
            return
        transaction = self.current_transactions[selected_row]
        transaction_id = transaction["id"]
        confirm = QMessageBox.question(
            self,
            "Delete",
            f"Delete transaction #{transaction_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.delete_btn.setEnabled(False)
        thread = NetworkThread(f"/transactions/{transaction_id}", method="DELETE", headers=self.headers())
        thread.result.connect(self.on_transaction_changed)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda: self.delete_btn.setEnabled(True))
        self._start_thread(thread)

    def on_transaction_changed(self, data):
        self.load_transactions()

    def setup_2fa(self):
        from setup_2fa_window import Setup2FAWindow

        dlg = Setup2FAWindow(self.token)
        dlg.exec()

    def show_statistics(self):
        self.stats_btn.setEnabled(False)
        thread = NetworkThread("/statistics", method="GET", headers=self.headers())
        thread.result.connect(self.on_statistics)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda: self.stats_btn.setEnabled(True))
        self._start_thread(thread)

    def on_statistics(self, data):
        total = data.get("total_amount", 0)
        count = data.get("total_transactions", 0)
        by_category = data.get("by_category", {})
        text = [f"Transactions: {count}", f"Total amount: {total:.2f}", "", "By category:"]
        for category, amount in by_category.items():
            text.append(f"- {category}: {amount:.2f}")
        self.result_text.setText("\n".join(text))

    def show_charts(self):
        self.charts_btn.setEnabled(False)
        thread = NetworkThread("/statistics", method="GET", headers=self.headers())
        thread.result.connect(self.on_charts_stats)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda: self.charts_btn.setEnabled(True))
        self._start_thread(thread)

    def on_charts_stats(self, data):
        from charts_window import ChartsWindow

        dlg = ChartsWindow(data, self)
        dlg.exec()

    def generate_report(self):
        self.generate_report_btn.setEnabled(False)
        self.result_text.setText("Report generation started in background...")
        thread = NetworkThread("/reports/generate", method="POST", headers=self.headers())
        thread.result.connect(self.on_report_generation_started)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda: self.generate_report_btn.setEnabled(True))
        self._start_thread(thread)

    def on_report_generation_started(self, data):
        self.current_report_id = data.get("report_id")
        self.result_text.setText(
            "Report generation started.\n"
            f"Report ID: {self.current_report_id}\n\n"
            "You can continue using the application.\n"
            "Press 'Check Report Status' after a few seconds."
        )

    def check_report_status(self):
        if not self.current_report_id:
            QMessageBox.warning(self, "Warning", "No report has been generated yet")
            return
        self.check_report_btn.setEnabled(False)
        thread = NetworkThread(f"/reports/{self.current_report_id}", method="GET", headers=self.headers())
        thread.result.connect(self.on_report_status)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda: self.check_report_btn.setEnabled(True))
        self._start_thread(thread)

    def on_report_status(self, data):
        self.result_text.setText(
            f"Report ID: {data.get('report_id')}\n"
            f"Status: {data.get('status')}\n"
            f"File: {data.get('file')}"
        )

    @Slot(str)
    def on_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.result_text.setText(f"Error: {msg}")
