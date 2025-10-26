import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsTextItem

from document import Document


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main.ui", self)

        doc = Document()
        self.tabWidget.addTab(doc.view, "Новый документ")

        doc = Document()
        self.tabWidget.addTab(doc.view, "Новый документ 2")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = AppWindow()
    ex.show()
    sys.exit(app.exec())
