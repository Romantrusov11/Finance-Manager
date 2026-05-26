from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChartsWindow(QDialog):
    def __init__(self, stats, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Statistics and Charts")
        self.setGeometry(250, 250, 800, 600)

        layout = QVBoxLayout()
        total = stats.get("total_amount", 0)
        count = stats.get("total_transactions", 0)
        by_category = stats.get("by_category", {})

        layout.addWidget(QLabel(f"Total transactions: {count}"))
        layout.addWidget(QLabel(f"Total amount: {total:.2f}"))

        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.draw_charts(by_category)

    def draw_charts(self, by_category):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if not by_category:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
            self.canvas.draw()
            return
        categories = list(by_category.keys())
        values = list(by_category.values())
        ax.bar(categories, values)
        ax.set_title("Expenses by category")
        ax.set_xlabel("Category")
        ax.set_ylabel("Amount")
        ax.tick_params(axis="x", rotation=30)
        self.canvas.draw()
