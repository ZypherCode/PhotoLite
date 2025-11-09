import math

from PyQt6 import uic
from PyQt6.QtWidgets import (QDialog, QTextEdit, QFontComboBox, QSpinBox,
                             QColorDialog, QPushButton, QMainWindow, QTextBrowser,
                             QVBoxLayout, QWidget)
from PyQt6.QtCore import Qt

class AboutForm(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("О программе")
        self.setGeometry(100, 100, 600, 400)  # Размер окошка, как тетрадь

        # Центральный виджет с лейаутом
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаём QTextBrowser
        self.text_browser = QTextBrowser()
        layout.addWidget(self.text_browser)

        # Добавляем текст с HTML
        html_text = """
        <h1>PhotoLite -</h1>
        <p>легкий графический редактор для рисования и работы со слоями.<br>
        Версия: 1.0<br>
        <br>
        Автор: <a style="color: rgb(9, 121, 187)" href="https://github.com/ZypherCode">ZypherCode</a><br>
        О проекте: <a style="color: rgb(9, 121, 187)" href="https://github.com/ZypherCode/PhotoLite">GitHub</a><br>
        Проект создан в учебных целях.<br><br>

        <h3>Источники:</h3>
        <p>
        Иконки: <a style="color: rgb(9, 121, 187)" href="https://svgrepo.com">svgrepo.com</a><br>
        Изображения: <a style="color: rgb(9, 121, 187)" href="https://ru.freepik.com">ru.freepik.com</a><br>
        Виджет colorpicker: <a style="color: rgb(9, 121, 187)" href="https://github.com/tomfln/pyqt-colorpicker-widget">GitHub</a><br>
        Кастомная рамка окна <a style="color: rgb(9, 121, 187)" href="https://stackoverflow.com/questions/44241612/custom-titlebar-with-frame-in-pyqt5">StackOwerflow</a><br>
        </p>
        2025</p>
        """
        self.text_browser.setHtml(html_text)

        # Чтобы ссылки открывались в браузере системы
        self.text_browser.setOpenExternalLinks(True)  # Без этого ссылки не кликабельны снаружи

class SecondForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/new.ui", self)

        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint)

        # связываем кнопки
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.spinBox.valueChanged.connect(self.on_spinbox_value_changed)
        self.spinBox_2.valueChanged.connect(self.on_spinbox_value_changed)

        self.comboBox.addItems(["White", "Transparent", "Red", "Black"])

    def on_spinbox_value_changed(self, value):
        width = self.spinBox.value()
        height = self.spinBox_2.value()

        # если фиксируем соотношение сторон
        if self.checkBox.isChecked():
            # разбираем текущее соотношение, например "16:9"
            ratio_text = self.label_5.text()
            try:
                ratio_w, ratio_h = map(int, ratio_text.split(":"))
            except ValueError:
                # если вдруг там что-то странное - по умолчанию 16:9
                ratio_w, ratio_h = 16, 9

            sender = self.sender()
            # определяем, какой spinBox изменён
            if sender == self.spinBox:
                # пересчитываем высоту
                new_height = round(width * ratio_h / ratio_w)
                self.spinBox_2.blockSignals(True)
                self.spinBox_2.setValue(new_height)
                self.spinBox_2.blockSignals(False)
            elif sender == self.spinBox_2:
                # пересчитываем ширину
                new_width = round(height * ratio_w / ratio_h)
                self.spinBox.blockSignals(True)
                self.spinBox.setValue(new_width)
                self.spinBox.blockSignals(False)
        else:
            # если галочка снята - просто показываем текущее соотношение
            common_divisor = math.gcd(width, height)
            ratio_width = width // common_divisor
            ratio_height = height // common_divisor
            self.label_5.setText(f"{ratio_width}:{ratio_height}")

    def get_values(self):
        """Возвращает данные формы в виде словаря"""
        return {
            "name": self.lineEdit.text() or "Безымянный проект",
            "width": self.spinBox.value(),
            "height": self.spinBox_2.value(),
            "background": self.comboBox.currentText()
        }
    
    
class SettingsForm(QDialog):
    def __init__(self, parent=None, layer=None):
        super().__init__(parent)
        uic.loadUi("ui/layer.ui", self)

        self.layer = layer

        if self.layer.type == "Text":
            self.edit = QTextEdit()
            self.edit.setText(self.layer.text)
            self.gridLayout_5.addWidget(self.edit, 0, 1, 3, 1)
            self.col = self.layer.text_color

            self.fontBox = QFontComboBox()
            try:
                self.fontBox.setCurrentFont(self.layer.font)
            except:
                pass
            self.gridLayout_5.addWidget(self.fontBox, 0, 0)

            self.fontSize = QSpinBox()
            self.fontSize.setMinimum(5)
            self.fontSize.setMaximum(2184)
            try:
                self.fontSize.setValue(self.layer.font.pixelSize())
            except:
                self.fontSize.setValue(12)
            self.gridLayout_5.addWidget(self.fontSize, 1, 0)
            self.button = QPushButton("Select color")
            self.button.setStyleSheet("color: rgba%s" 
                                   % str(self.layer.text_color.getRgb()))
            self.button.clicked.connect(self.showDialog)
            self.gridLayout_5.addWidget(self.button, 2, 0)


        # связываем кнопки
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.horizontalSlider.valueChanged.connect(self.value_changed)

        self.lineEdit.setText(self.layer.name)
        self.checkBox.setChecked(self.layer.visible)
        self.checkBox_2.setChecked(self.layer.locked)
        self.horizontalSlider.setValue(int(self.layer.opacity*100))

        if self.layer.name == "Background":
            self.lineEdit.setDisabled(True)
            self.checkBox_2.setDisabled(True)
            self.checkBox_2.setChecked(True)

        try:
            self.spinBox.setValue(int(self.layer.scale))
        except:
            self.spinBox.setDisabled(True)

        self.label_3.setText(f"Opacity: {int(self.layer.opacity*100)}%")

    def showDialog(self):
        self.col = QColorDialog.getColor()
        if self.col.isValid():
            self.button.setStyleSheet("color: rgba%s" 
                                   % str(self.col.getRgb()))
        

    def value_changed(self):
        self.label_3.setText(f"Opacity: {self.horizontalSlider.value()}%")

    def get_values(self):
        """Возвращает данные формы в виде словаря"""
        out =  {
            "name": self.lineEdit.text(),
            "visible": self.checkBox.isChecked(),
            "locked": self.checkBox_2.isChecked(),
            "opacity": self.horizontalSlider.value(),
            "scale": self.spinBox.value()
        }

        if self.layer.type == "Text":
            font = self.fontBox.currentFont()
            font.setPixelSize(self.fontSize.value())
            out["text"] = self.edit.toPlainText()
            out["font"] = font
            out["color"] = self.col

        return out

class NewLayerForm(QDialog):
    def __init__(self, parent=None, name="Слой"):
        super().__init__(parent)
        uic.loadUi("ui/new_layer.ui", self)
        self.name = name

        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self.comboBox.addItems(["Transparent", "White", "Red", "Black"])

        self.lineEdit.setText(name)
        self.lineEdit.setFocus()
        self.lineEdit.selectAll()

    def get_values(self):
        """Возвращает данные формы в виде словаря"""
        return {
            "name": self.lineEdit.text() or self.name,
            "opacity": self.spinBox.value(),
            "background": self.comboBox.currentText()
        }