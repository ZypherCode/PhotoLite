import sys, math
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QDialog, QMessageBox, QTextEdit, QFontComboBox, QSpinBox
from PyQt6.QtGui import QPixmap
from document import Document
from tools import Hand, Editor
from PyQt6.QtCore import QRectF, Qt

from superqt import QFlowLayout
from colorpicker import ColorPicker

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main.ui", self)

        self.documents = [] # Список документов

        # Событие переключения и закрытия вкладки
        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        self.tabWidget.tabCloseRequested.connect(self.closeDoc) # self.tabWidget.removeTab

        self.picker = ColorPicker()
        self.gridLayout_5.addWidget(self.picker, 0, 0)

        # Кнопка добавления слоя
        if hasattr(self, "btnAddLayer"):
            self.btnAddLayer.clicked.connect(self.add_layer_to_active)
        self.btnAddImage.clicked.connect(self.add_image_layer_to_active)
        self.btnDeleteLayer.clicked.connect(self.delete_layer)
        self.btnUpLayer.clicked.connect(self.replace_layer)
        self.btnDownLayer.clicked.connect(self.replace_layer)
        self.btnSettingsLayer.clicked.connect(self.open_layer_settings)

        self.loolsGroup.buttonClicked.connect(self.changeTool)

        self.saveAct.triggered.connect(self.saveDoc)
        self.addAct.triggered.connect(self.add_image_layer_to_active)
        self.newAct.triggered.connect(self.newDoc)

        self.listLayers.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        if not self.listLayers.selectedItems() and self.listLayers.count() > 0:
            # Если выделение исчезло — вернуть предыдущее
            self.listLayers.setCurrentRow(0)

    def closeEvent(self, event):
        """Перехватывает закрытие главного окна"""
        # если нет документов — просто закрываем
        if not self.documents:
            event.accept()
            return

        # проходим по всем документам
        for i in range(len(self.documents) - 1, -1, -1):
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Закрытие документа")
            dlg.setText(f"Сохранить изменения в «{self.documents[i].name}»?")
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            dlg.setIcon(QMessageBox.Icon.Question)
            button = dlg.exec()

            if button == QMessageBox.StandardButton.Save:
                self.saveDoc(self.documents[i])
            elif button == QMessageBox.StandardButton.Cancel:
                # отменяем закрытие всего приложения
                event.ignore()
                return
            # если Discard — просто удаляем
            self.documents.pop(i)
            self.tabWidget.removeTab(i)

        # если цикл завершился — разрешаем закрытие
        event.accept()


    def closeDoc(self, index):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Закрытие документа")
        dlg.setText(f"Сохранить изменения в «{self.documents[index].name}»?")
        dlg.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Close | QMessageBox.StandardButton.No)
        dlg.setIcon(QMessageBox.Icon.Question)
        button = dlg.exec()

        if button == QMessageBox.StandardButton.Save:
            self.saveDoc(self.documents[index])
        elif button == QMessageBox.StandardButton.Close:
            return
        
        self.documents.pop(index)
        self.tabWidget.removeTab(index)
        self.listLayers.clear()

    def newDoc(self):
        dialog = SecondForm(self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            data = dialog.get_values()
            if data["background"] == "Transparent":
                bg_color = Qt.GlobalColor.transparent
            elif data["background"] == "White":
                bg_color = Qt.GlobalColor.white
            elif data["background"] == "Red":
                bg_color = Qt.GlobalColor.red
            elif data["background"] == "Black":
                bg_color = Qt.GlobalColor.black

            self.add_new_document(
                data["name"],
                data["width"],
                data["height"],
                bg_color
            )

    def saveDoc(self, doc=None):
        if not doc:
            doc = self.get_active_document()
        doc.export_area(f"{doc.name}.png", QRectF(0, 0, doc.width, doc.height))

    def changeTool(self, button):
        doc = self.get_active_document()
        if button is self.toolHand:
            doc.changeTool(Hand())
        else:
            doc.changeTool(Editor())

    def add_new_document(self, name, w, h, bg):
        """Создает и добавляет новый документ как вкладку."""
        doc = Document(name, w, h, bg)
        self.documents.append(doc)
        self.tabWidget.addTab(doc, name)
        self.tabWidget.setCurrentWidget(doc)
        self.picker.setRGB(doc.color)
        self.update_layer_list(doc)

    def get_active_document(self):
        """Возвращает текущий активный документ (вкладку)."""
        index = self.tabWidget.currentIndex()
        if 0 <= index < len(self.documents):
            return self.documents[index]
        return None

    def add_layer_to_active(self):
        """Добавляет слой только в активный документ."""
        doc = self.get_active_document()
        if doc:
            #layer = doc.layers.add_layer(f"Слой {len(doc.layers._layers)}")
            doc.add_solid_layer(f"Слой {len(doc.layers._layers)}")
            self.update_layer_list(doc)

    def add_image_layer_to_active(self):
        doc = self.get_active_document()
        filename, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "", "Images (*.png *.jpg *.bmp)")
        if not filename:
            return  # пользователь отменил
        
        pixmap = QPixmap(filename)
        doc.add_pixmap_layer(filename.split('/')[-1], pixmap)
        self.update_layer_list(doc)

    def open_layer_settings(self):
        doc = self.get_active_document()
        layer = doc.get_layer(self.listLayers.currentRow())
        dialog = SettingsForm(self, layer)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            data = dialog.get_values()
            if data["name"]:
                layer.set_name(data["name"])
            layer.set_opacity((data["opacity"]+1)/100)
            layer.set_visible(data["visible"])
            layer.set_locked(data["locked"])
            layer.set_scale(data["scale"]/100)
            
            try:
                if data["text"]:
                    layer.set_text(data["text"])
                if data["font"]:
                    layer.set_font(data["font"])
            except KeyError:
                pass

        self.update_layer_list(doc)


    def update_layer_list(self, doc, direction=0):
        """Обновляет список слоев (listLayers) в интерфейсе для конкретного документа."""
        current = self.listLayers.currentRow()
        if hasattr(self, "listLayers"):
            self.listLayers.clear()
            self.listLayers.addItems(doc.layers.list_layers())
        
        if current != -1 and current < self.listLayers.count():
            self.listLayers.setCurrentRow(current+direction)
        elif self.listLayers.count() > 0:
            self.listLayers.setCurrentRow(0)


    def replace_layer(self):
        try:
            doc = self.get_active_document()
            direction = self.sender().text() == "Up"
            doc.move_layer(self.listLayers.currentRow(), direction)
            print(1-direction)
            self.update_layer_list(doc, 1-direction)
        except IndexError:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Layer not selected!")
            dlg.setText("Please select a layer first.")
            dlg.exec()

    def delete_layer(self):
        try:
            doc = self.get_active_document()
            doc.remove_layer(self.listLayers.currentRow())
            self.update_layer_list(doc)
        except IndexError:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Layer not selected!")
            dlg.setText("Please select a layer first.")
            dlg.exec()

    def on_tab_changed(self, index):
        """Переключение вкладки — обновляем список слоев под новый документ."""
        doc = self.get_active_document()
        if doc:
            self.update_layer_list(doc)

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

        self.comboBox.addItems(["Transparent", "White", "Red", "Black"])

    def on_spinbox_value_changed(self, value):
        width = self.spinBox.value()
        height = self.spinBox_2.value()
        print(self.comboBox.currentText())

        # если фиксируем соотношение сторон
        if self.checkBox.isChecked():
            # разбираем текущее соотношение, например "16:9"
            ratio_text = self.label_5.text()
            try:
                ratio_w, ratio_h = map(int, ratio_text.split(":"))
            except ValueError:
                # если вдруг там что-то странное — по умолчанию 16:9
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
            # если галочка снята — просто показываем текущее соотношение
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
            self.gridLayout_5.addWidget(self.edit, 0, 1)

            self.fontBox = QFontComboBox()
            try:
                self.fontBox.setCurrentFont(self.layer.font)
            except:
                pass
            self.gridLayout_5.addWidget(self.fontBox, 0, 0)

            self.fontSize = QSpinBox()
            self.fontSize.setMinimum(5)
            self.fontSize.setMaximum(100)
            try:
                self.fontSize.setValue(self.layer.font.pixelSize())
            except:
                pass
            self.gridLayout_5.addWidget(self.fontSize, 1, 0)

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

        return out

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
