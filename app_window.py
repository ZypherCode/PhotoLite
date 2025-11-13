"""
Главный файл приложения.
Логика ui
"""

import sys, psutil, math
from random import randint
from datetime import datetime

from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QDialog, 
                             QMessageBox, QWidget, QVBoxLayout, QListWidgetItem, 
                             QLabel, QProgressDialog)
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtCore import QRectF, Qt, QSize, QTimer

from colorpicker import ColorPicker
from document import Document
from tools import Hand, Editor
from file_logic import SaveDoc, OpenDoc, NotCorrectFolder

from ui.widgets.bar import MyBar
from ui.widgets.layer_item import LayerItem
from ui.widgets.forms import SecondForm, NewLayerForm, SettingsForm, AboutForm


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
        self.easter_counter = 0
        self.easter_stage = 0

        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        self.tabWidget.tabCloseRequested.connect(self.close_doc)

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
        self.checkSoft.stateChanged.connect(self.change_hardness)

        # Менюбар
        self.saveAct.triggered.connect(self.save_doc)
        self.openAct.triggered.connect(self.open_doc)
        self.actionExport.triggered.connect(self.export)
        self.addAct.triggered.connect(self.add_image_layer_to_active)
        self.newAct.triggered.connect(self.new_doc)
        self.actionClose.triggered.connect(lambda: self.close_doc(self.listLayers.currentRow()))
        self.actionCloseAll.triggered.connect(self.close_all)
        self.actionExit.triggered.connect(self.close)
        self.actionGetComposite.triggered.connect(self.add_composite_layer)
        self.actionAddEmptyLayer.triggered.connect(self.add_empty_layer)
        self.newLayer.triggered.connect(self.add_layer_to_active)
        self.delAct.triggered.connect(self.delete_layer)
        self.aboutAct.triggered.connect(self.open_about)

        # Инструменты
        self.actionHand.triggered.connect(self.change_tool)
        self.actionMoveTool.triggered.connect(self.change_tool)
        self.actionBrush.triggered.connect(self.change_tool)
        self.actionErasier.triggered.connect(self.change_tool)

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
        self.checkSoft.hide()

        self.process = psutil.Process()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_widget)
        self.timer.start(350)

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
        self.easter_counter =+ int(self.easter_counter >= 0)

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

    def close_all(self):
        for i in range(len(self.documents) - 1, -1, -1):
            self.close_doc(i)

    def closeEvent(self, event):
        """если закрыл окно и не сохранил"""
        if not self.documents:
            event.accept()
            return

        # на момент написания данного комментария я 
        # благополучно забыл зачем инвертировать  список :)
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
                self.save_doc(self.documents[i])
            elif button == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

            self.documents.pop(i)
            self.tabWidget.removeTab(i)
        event.accept()

    def open_about(self):
        form = AboutForm(self)
        form.show()

    def close_doc(self, index):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Закрытие документа")
        dlg.setText(f"Сохранить изменения в «{self.documents[index].name}»?")
        dlg.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Close | QMessageBox.StandardButton.No)
        dlg.setIcon(QMessageBox.Icon.Question)
        button = dlg.exec()

        if button == QMessageBox.StandardButton.Save:
            self.save_doc(self.documents[index])
        elif button == QMessageBox.StandardButton.Close:
            return
        
        self.documents.pop(index)
        self.tabWidget.removeTab(index)
        self.listLayers.clear()

    def open_doc(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выбрать проект", "", "PhotoLite (*.pld)")
        if not filename:
            return
        try:
            dc = OpenDoc(filename)
            doc, ver = dc.get_opened_document()
            if ver > doc.sys_version:
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Конфликт совместимости")
                dlg.setText(f"""Проект «{doc.name}» создан в PhotoLite {ver}, но у вас стоит более ранняя версия {doc.sys_version}
Рекомендуем обновить программу или создать резервную копию, иначе Вы можете повредить проект. 
Продолжить?""")
                dlg.setStandardButtons(
                    QMessageBox.StandardButton.Ok |
                    QMessageBox.StandardButton.No
                )
                dlg.setDefaultButton(QMessageBox.StandardButton.No)
                dlg.setIcon(QMessageBox.Icon.Warning)
                button = dlg.exec()

                if button == QMessageBox.StandardButton.No:
                    return
            
            self.documents.append(doc)
            self.tabWidget.addTab(doc, doc.name)
            self.tabWidget.setCurrentWidget(doc)
            self.picker.setRGB(doc.color.getRgb()[:-1])
            self.update_layer_list(doc)
            doc.filepath = filename
        except Exception:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Ошибка")
            dlg.setText(f"PhotoLite не удалось открыть «{filename}», так как файл поврежден или не поддерживается.")
            dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
            dlg.setIcon(QMessageBox.Icon.Critical)
            button = dlg.exec()

    def new_doc(self):
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

    def save_doc(self, doc=None):
        doc = self.get_active_document()
        if doc and doc.filepath:
            dirname = doc.filepath
        else:
            dirname, _ = QFileDialog.getSaveFileName(self, "Save as", ".", "PhotoLite (*.pld)")
            if not dirname:
                return
            doc.filepath = dirname

        dlg = QProgressDialog("Сохранение...", None, 0, 100, self)
        dlg.setWindowTitle("PhotoLite")
        dlg.setCancelButton(None)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.show()
        dlg.setValue(randint(21, 37)) # Случайный прогресс. По-моему забавно :)

        QApplication.processEvents()

        SaveDoc(doc, dirname)
        doc.modified = datetime.now().timestamp()

        dlg.setValue(100)
        dlg.close()

    def export(self):
        doc = self.get_active_document()
        if not doc:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export to", ".", file_filter)
        if not filename:
            return
        doc.export_area(filename, QRectF(0, 0, doc.width, doc.height))

    def change_brush(self, value):
        doc = self.get_active_document()
        if not doc:
            return
        doc.brush.width = value
    
    def change_hardness(self, state):
        doc = self.get_active_document()
        if not doc:
            return
        doc.brush.hardness = (state != 0) * 100

    def change_tool(self, button):
        doc = self.get_active_document()
        if not doc:
            return
        self.label_3.hide()
        self.brushSize.hide()
        self.checkSoft.hide()
        if self.sender() is self.actionHand:
            doc.changeTool(Hand())
            self.label_4.setText("Hand")
        elif self.sender() is self.actionMoveTool:
            self.easter()
            doc.changeTool(Editor())
            self.label_4.setText("Move tool")
        elif self.sender() is self.actionBrush or self.sender() is self.actionErasier:
            doc.changeTool(doc.brush)
            self.label_4.setText("Brush")
            self.label_3.show()
            self.brushSize.show()
            self.checkSoft.show()
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
        doc.add_layer(f"Слой {len(doc.layers._layers)}")
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
        
        dialog = NewLayerForm(self, f"Слой {len(doc.layers._layers)}")
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

            pixmap = QPixmap(doc.width, doc.height)
            pixmap.fill(bg_color)
            doc.add_pixmap_layer(data["name"], pixmap)
            layer = doc.get_layer(0)
            layer.set_opacity(data["opacity"] / 100)
            self.update_layer_list(doc)
            self.listLayers.setCurrentRow(0)

    def add_text_layer_to_active(self):
        doc = self.get_active_document()
        if not doc:
            return
        doc.add_text_layer("Lorem ipsum", "Lorem ipsum")
        self.update_layer_list(doc)

    def add_image_layer_to_active(self):
        doc = self.get_active_document()
        filename, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "", "Images (*.png *.jpg *.bmp *.jpeg *.gif *.pbm *.pgm *.ppm *.xbm *.xpm)")
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

        self.textBrowser.setHtml(get_doc_html(doc))

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
            self.listLayers.setCurrentRow(0)
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
        
    def easter(self):
        self.easter_counter += 1
        if self.easter_counter > 3:
            if self.easter_stage == 0:
                self.actionMoveTool.setIcon(QIcon("ui\\icons\\egg1.svg"))
                self.easter_stage += 1
            elif self.easter_stage == 1:
                self.actionMoveTool.setIcon(QIcon("ui\\icons\\egg2.svg"))
                self.easter_stage += 1
            elif self.easter_stage == 2:
                self.actionMoveTool.setIcon(QIcon("ui\\icons\\egg3.svg"))
                self.easter_stage += 1
            elif self.easter_stage >= 3:
                self.actionMoveTool.setIcon(QIcon("ui\\icons\\egg4.svg"))
                self.easter_stage += 1
                self.easter_counter = 0


file_filter = (
    "Поддерживаемые изображения (*.bmp *.gif *.jpg *.jpeg *.png *.pbm *.pgm *.ppm *.xbm *.xpm);;"
    "Portable Network Graphics (*.png);;"
    "Joint Photographic Experts Group (*.jpeg);;"
    "Windows Bitmap (*.bmp);;"
    "Graphics Interchange Format (*.gif);;"
    "Portable Bitmap (*.pbm);;"
    "Portable Graymap (*.pgm);;"
    "Portable Pixmap (*.ppm);;"
    "X11 Bitmap (*.xbm);;"
    "X11 Pixmap (*.xpm)"
)


def get_doc_html(doc):
    common_divisor = math.gcd(doc.width, doc.height)
    ratio_width = doc.width // common_divisor
    ratio_height = doc.height // common_divisor
    ratio = f"{ratio_width}:{ratio_height}"

    created = datetime.fromtimestamp(doc.created).strftime('%Y-%m-%d %H:%M:%S')
    if doc.modified:
        modified = datetime.fromtimestamp(doc.modified).strftime('%Y-%m-%d %H:%M:%S')
    else:
        modified = "Никогда"

    html_text = f"""
        <h1>{doc.name}</h1>
        <p>
        {doc.dsc.replace("\n", "<br>")}<br><br>

        Размеры: {doc.width}/{doc.height} ({ratio})<br>
        Создан: {created} в PhotoLite {doc.version}<br>
        Изменен: {modified}<br>
        </p>
        """

    return html_text

if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open("ui\\dark.qss", "r") as f:
        app.setStyleSheet(f.read())
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
