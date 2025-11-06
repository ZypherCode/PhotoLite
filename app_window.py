import sys, math, psutil
from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QDialog, 
                             QMessageBox, QTextEdit, QFontComboBox, QSpinBox,
                             QWidget, QVBoxLayout, QListWidgetItem, QLabel, QColorDialog,
                             QPushButton)
from PyQt6.QtGui import QPixmap, QIcon, QColor
from document import Document
from tools import Hand, Editor, BrushTool
from PyQt6.QtCore import QRectF, Qt, QSize, QTimer

from colorpicker import ColorPicker
from ui.widgets.bar import MyBar
from ui.widgets.layer_item import LayerItem

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main.ui", self)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # кастомную шапку
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.titlebar = MyBar(self)
        layout.addWidget(self.titlebar)

        # основное содержимое в центральный виджет
        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.centralWidget())
        layout.addWidget(main)
        self.setCentralWidget(container)
        self.titlebar.setParent(self)
        self.titlebar.move(0, 0)
        self.titlebar.raise_()
        self.setContentsMargins(0, self.titlebar.height(), 0, 0)

        self.documents = []

        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        self.tabWidget.tabCloseRequested.connect(self.closeDoc)

        # кастомный колорпикер 
        self.picker = ColorPicker()
        self.picker.colorChanged.connect(self.set_color_to_active)
        self.gridLayout_5.addWidget(self.picker, 0, 0)

        # Слоты
        self.btnAddLayer.clicked.connect(self.add_layer_to_active)
        self.btnAddImg.clicked.connect(self.add_image_layer_to_active)
        self.btnDeleteLayer.clicked.connect(self.delete_layer)
        self.btnUpLayer.clicked.connect(self.replace_layer)
        self.btnDownLayer.clicked.connect(self.replace_layer)
        self.btnSettingsLayer.clicked.connect(self.open_layer_settings)
        self.btnAddTxt.clicked.connect(self.add_text_layer_to_active)
        self.checkBoxLock.stateChanged.connect(self.lock_layer)
        self.spinBoxOpacity.valueChanged.connect(self.opacity_layer)
        self.brushSize.valueChanged.connect(self.change_brush)

        # Менюбар
        self.saveAct.triggered.connect(self.saveDoc)
        self.addAct.triggered.connect(self.add_image_layer_to_active)
        self.newAct.triggered.connect(self.newDoc)
        self.actionClose.triggered.connect(lambda: self.closeDoc(self.listLayers.currentRow()))
        self.actionCloseAll.triggered.connect(self.closeAll)
        self.actionExit.triggered.connect(self.close)
        self.actionGetComposite.triggered.connect(self.add_composite_layer)
        self.actionAddEmptyLayer.triggered.connect(self.add_empty_layer)

        # Инструменты
        self.actionHand.triggered.connect(self.changeTool)
        self.actionMoveTool.triggered.connect(self.changeTool)
        self.actionBrush.triggered.connect(self.changeTool)
        self.actionErasier.triggered.connect(self.changeTool)

        # Иконки
        self.actionHand.setIcon(QIcon("ui\\icons\\hand.svg"))
        self.actionBrush.setIcon(QIcon("ui\\icons\\brush.svg"))
        self.actionMoveTool.setIcon(QIcon("ui\\icons\\move.svg"))
        self.actionErasier.setIcon(QIcon("ui\\icons\\eraser.svg"))
        self.btnDeleteLayer.setIcon(QIcon("ui\\icons\\bin.svg"))
        self.btnUpLayer.setIcon(QIcon("ui\\icons\\up.svg"))
        self.btnDownLayer.setIcon(QIcon("ui\\icons\\down.svg"))
        self.btnAddLayer.setIcon(QIcon("ui\\icons\\plus.svg"))
        self.btnSettingsLayer.setIcon(QIcon("ui\\icons\\settings.svg"))
        self.btnAddTxt.setIcon(QIcon("ui\\icons\\text.svg"))
        self.btnAddImg.setIcon(QIcon("ui\\icons\\image.svg"))
        self.titlebar.title.setPixmap(QPixmap("ui\\icons\\logo.svg").scaledToHeight(18))

        # Чтобы выделение слоя не пропадало
        self.listLayers.selectionModel().selectionChanged.connect(self.on_selection_changed)

        self.label_3.hide()
        self.brushSize.hide()

        self.process = psutil.Process()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_widget)
        self.timer.start(200)

    def update_widget(self):
        memory_in_bytes = self.process.memory_info().rss
        memory_in_kb = memory_in_bytes / 1024
        memory_in_mb = memory_in_kb / 1024 
        memory_in_gb = memory_in_mb / 1024
        processor = self.process.cpu_percent() / len(self.process.cpu_affinity())
        out = ""
        if memory_in_gb < 1:
            out += f"Используемая память: {memory_in_mb:.2f} Мбайт"
        elif memory_in_mb < 1:
            out += f"Используемая память: {memory_in_kb:.2f} Кбайт"
        else:
            out += f"Используемая память: {memory_in_gb:.2f} Гбайт"

        out += f", процессор: {processor:.1f}%"
        self.statusbar.showMessage(out)

    def on_selection_changed(self, selected, deselected):
        if self.listLayers.currentRow() == -1 and self.listLayers.count() > 0:
            # Если выделение исчезло - вернуть предыдущее
            self.listLayers.setCurrentRow(0)
        doc = self.get_active_document()
        if not doc:
            return
        layer = doc.get_layer(self.listLayers.currentRow())
        self.spinBoxOpacity.setValue(int(layer.opacity*100))
        self.checkBoxLock.setChecked(layer.locked)
        doc.active_layer = layer

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.titlebar.setFixedWidth(self.width())

    def exit(self):
        try:
            self.closeEvent
        except AttributeError:
            pass

    def closeAll(self):
        for i in range(len(self.documents) - 1, -1, -1):
            self.closeDoc(i)

    def closeEvent(self, event):
        """если закрыл окно и не сохранил"""
        if not self.documents:
            event.accept()
            return

        # на момент написания данного комментария я 
        # благополучно забыл зачем инвертировать список :)
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
                event.ignore()
                return

            self.documents.pop(i)
            self.tabWidget.removeTab(i)
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
                data["height"]
            )
            doc = self.get_active_document()
            doc.add_solid_layer("Bg", locked=True, color=bg_color)
            self.update_layer_list(doc)
            self.listLayers.setCurrentRow(0)

    def saveDoc(self, doc=None):
        doc = self.get_active_document()
        if not doc:
            return
        doc.export_area(f"{doc.name}.png", QRectF(0, 0, doc.width, doc.height))

    def change_brush(self, value):
        doc = self.get_active_document()
        if not doc:
            return
        doc.brush.width = value

    def changeTool(self, button):
        doc = self.get_active_document()
        if not doc:
            return
        self.label_3.hide()
        self.brushSize.hide()
        if self.sender() is self.actionHand:
            doc.changeTool(Hand())
            self.label_4.setText("Hand")
        elif self.sender() is self.actionMoveTool:
            doc.changeTool(Editor())
            self.label_4.setText("Move tool")
        elif self.sender() is self.actionBrush or self.sender() is self.actionErasier:
            doc.changeTool(doc.brush)
            self.label_4.setText("Brush")
            self.label_3.show()
            self.brushSize.show()
        doc.erasier = self.sender() is self.actionErasier

    def add_new_document(self, name, w, h):
        """Создает и добавляет новый документ как вкладку."""
        doc = Document(name, w, h)
        self.documents.append(doc)
        self.tabWidget.addTab(doc, name)
        self.tabWidget.setCurrentWidget(doc)
        self.picker.setRGB(doc.color.getRgb()[:-1])
        self.update_layer_list(doc)

    def set_color_to_active(self):
        doc = self.get_active_document()
        if not doc:
            return
        doc.color = QColor(*list(map(int, self.picker.getRGB())))

    def add_empty_layer(self):
        doc = self.get_active_document()
        if not doc:
            return
        doc.add_layer("Empty")
        self.update_layer_list(doc)

    def add_composite_layer(self):
        doc = self.get_active_document()
        if not doc:
            return
        composite = doc.get_composite()
        doc.add_pixmap_layer("Composite", composite)
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
        if not doc:
            return
        doc.add_solid_layer(f"Слой {len(doc.layers._layers)}")
        self.update_layer_list(doc)

    def add_text_layer_to_active(self):
        doc = self.get_active_document()
        if not doc:
            return
        doc.add_text_layer("Lorem ipsum", "Lorem ipsum")
        self.update_layer_list(doc)

    def add_image_layer_to_active(self):
        doc = self.get_active_document()
        filename, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "", "Images (*.png *.jpg *.bmp *.jpeg)")
        if not filename:
            return
        
        pixmap = QPixmap(filename)
        if not doc:
            self.add_new_document(filename.split('/')[-1], pixmap.width(), pixmap.height())
        doc = self.get_active_document()
        doc.add_pixmap_layer(filename.split('/')[-1], pixmap)
        self.update_layer_list(doc)

    def open_layer_settings(self):
        doc = self.get_active_document()
        if not doc:
            return
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
                layer.set_color(data["color"])
            except KeyError:
                pass

        self.update_layer_list(doc)


    def update_layer_list(self, doc, direction=0):
        """Обновляет список слоев (listLayers) в интерфейсе для конкретного документа."""
        current = self.listLayers.currentRow()
        self.listLayers.clear()
        for layer in doc.layers._layers[::-1]:
            if layer is doc.bg_layer:
                continue
            item = QListWidgetItem()
            widget = LayerItem(layer.name, layer.visible, layer.locked)
            item.setSizeHint(widget.sizeHint())
            self.listLayers.addItem(item)
            self.listLayers.setItemWidget(item, widget)
            if hasattr(widget, "lock"):
                widget.lock.setPixmap(QPixmap("ui\\icons\\lock.svg").scaledToHeight(13))
            preview = layer.get_preview(QSize(32, 32))
            widget.icon = QLabel()
            widget.icon.setPixmap(preview)
            widget.layout.insertWidget(1, widget.icon)
            widget.toggled.connect(self.on_layer_toggled)
            widget.nameChanged.connect(self.on_layer_renamed)
            widget.settingsOpened.connect(self.on_layer_settings)

        if current != -1 and current < self.listLayers.count():
            self.listLayers.setCurrentRow(current+(direction*2)-1)
        elif self.listLayers.count() > 0:
            self.listLayers.setCurrentRow(0)

    def on_layer_toggled(self, widget, visible):
        # находим элемент списка, которому принадлежит этот widget...
        for i in range(self.listLayers.count()):
            if self.listLayers.itemWidget(self.listLayers.item(i)) == widget:
                self.listLayers.setCurrentRow(i)  # ...и выделяем его
                break

        # и теперь можно обновить видимость слоя
        doc = self.get_active_document()
        if not doc:
            return
        layer = doc.get_layer(self.listLayers.currentRow())
        if layer.name != "Background":
            layer.set_visible(visible)
        else:
            widget.checkbox.setChecked(True)

    def on_layer_renamed(self, widget, new_name):
        doc = self.get_active_document()
        if not doc:
            return
        layer = doc.get_layer(self.listLayers.currentRow())
        if layer.name != "Background":
            layer.set_name(new_name)
            self.update_layer_list(doc)

    def on_layer_settings(self, widget):
        self.open_layer_settings()

    def opacity_layer(self, value):
        doc = self.get_active_document()
        if not doc:
            return
        current = self.listLayers.currentRow()
        layer = doc.get_layer(current)
        if layer.name != "Background":
            layer.set_opacity(value/100)
        item = self.listLayers.item(current)
        widget = self.listLayers.itemWidget(item)
        preview = layer.get_preview(QSize(32, 32))
        widget.icon.setPixmap(preview)

    def lock_layer(self, state):
        doc = self.get_active_document()
        if not doc:
            return
        current = self.listLayers.currentRow()
        layer = doc.get_layer(current)
        layer.set_locked(state)
            # обновляем только нужный item
        item = self.listLayers.item(current)
        widget = self.listLayers.itemWidget(item)
        if state:
            widget.lock.show()
            widget.label.setStyleSheet("background: none; font-style: italic;")
        else:
            widget.lock.hide()
            widget.label.setStyleSheet("background: none; font-style: normal;")

    def replace_layer(self):
        try:
            doc = self.get_active_document()
            if not doc:
                return
            direction = self.sender().text() == "Up"
            doc.move_layer(self.listLayers.currentRow(), direction)
            self.update_layer_list(doc, 1-direction)
        except IndexError:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Layer not selected!")
            dlg.setText("Please select a layer first.")
            dlg.exec()

    def delete_layer(self):
        try:
            doc = self.get_active_document()
            if not doc:
                return
            doc.remove_layer(self.listLayers.currentRow())
            self.update_layer_list(doc)
        except IndexError:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Layer not selected!")
            dlg.setText("Please select a layer first.")
            dlg.exec()

    def on_tab_changed(self, index):
        """Переключение вкладки - обновляем список слоев под новый документ."""
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open("ui\\dark.qss", "r") as f:
        app.setStyleSheet(f.read())
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
