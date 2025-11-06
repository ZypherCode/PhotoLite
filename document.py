from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsItem
from canvas import CanvasScene, CanvasView
from layer import LayerManager, Layer, Solid, Image, Text
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor
from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import QRectF, QSize
from tools import BrushTool, Editor

class Document(QWidget):
    def __init__(self, name="Новый документ", width=1280, height=720):
        super().__init__()
        self.name = name
        self.width = width
        self.height = height
        self.activeTool = Editor()
        self.brush = BrushTool()
        self.color = QColor(255, 0, 0)
        self.erasier = False

        # Сцена и вью
        self.scene = CanvasScene()
        self.view = CanvasView(self.scene, self)
        self.scene.setSceneRect(0, 0, width, height)

        # Менеджер слоёв
        self.layers = LayerManager(self.scene)
        self.add_bg_layer()

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        #self.export_area("part.png", QRectF(100, 100, 400, 300))

    def move_layer(self, index, direction):
        index = len(self.layers._layers) - index - 1
        self.layers.move(index, direction)

    def set_active_layer(self, index):
        self.active_layer = self.get_layer(index)

    def remove_layer(self, index):
        index = len(self.layers._layers) - index - 1
        if self.layers._layers[index].name != "Background":
            self.layers.remove(index)

    def changeTool(self, tool):
        if tool.type == "Hand":
            self.view.drag(True)
            self.lock_all(True)
        else:
            self.view.drag(False)
            self.lock_all(False)
        self.activeTool = tool
        if tool.type == "Brush":
            self.brush = tool

    def lock_all(self, isMove):
        for item in self.layers._layers:
            if item.locked:
                continue
            item.group.setFlag(item.group.GraphicsItemFlag.ItemIsSelectable, not isMove)
            item.group.setFlag(item.group.GraphicsItemFlag.ItemIsMovable, not isMove)

    def add_solid_layer(self, name, locked=False, color=Qt.GlobalColor.white):
        lyr = Solid(name, self.scene, color, self.width, self.height)
        lyr.set_locked(locked)
        self.layers.add_layer(layer=lyr)

    def add_pixmap_layer(self, name, pixmap):
        lyr = Image(name, self.scene, pixmap, self.width, self.height)
        lyr.set_locked(False)
        self.layers.add_layer(layer=lyr)

    def add_text_layer(self, name, text):
        lyr = Text(name, self.scene, text=text)
        lyr.set_locked(False)
        self.layers.add_layer(layer=lyr)

    def get_layer(self, index):
        index = len(self.layers._layers) - index - 1
        return self.layers._layers[index]

    def add_bg_layer(self):
        """Добавляет слой-фон с шахматками для прозрачности"""
        checker = QPixmap(20, 20)
        checker.fill(QColor("lightGray"))
        painter = QPainter(checker)
        painter.fillRect(0, 0, 10, 10, QColor("white"))
        painter.fillRect(10, 10, 10, 10, QColor("white"))
        painter.end()

        bg_brush = QBrush(checker)
        rect_item = QGraphicsRectItem(self.scene.sceneRect())
        rect_item.setBrush(bg_brush)
        rect_item.setZValue(-1) 
        self.scene.addItem(rect_item)

        self.bg_layer = Layer("Background", self.scene, Qt.GlobalColor.transparent, self.width, self.height)
        self.bg_layer.group.addToGroup(rect_item)
        self.bg_layer.set_locked(True)
        self.layers.add_layer(layer=self.bg_layer) 
        self.bg_item = rect_item  # храним ссылку, чтобы скрывать при экспорте

    def add_layer(self, name, color=None):
        empty = QPixmap(QSize(self.width, self.height))
        empty.fill(Qt.GlobalColor.transparent)
        layer = Image(name, self.scene, empty, self.width, self.height)
        self.layers.add_layer(layer=layer)
        self.active_layer = layer

    def export_area(self, filename: str, rect: QRectF = None):
        """Экспортирует область сцены в PNG с прозрачным фоном"""
        if rect is None:
            rect = self.scene.sceneRect()

        if hasattr(self, "bg_item"):
            self.bg_item.setVisible(False)  # скрываем фон

        width, height = int(rect.width()), int(rect.height())
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)  # прозрачный фон

        painter = QPainter(pixmap)
        self.scene.render(painter, target=QRectF(pixmap.rect()), source=rect)
        painter.end()

        if hasattr(self, "bg_item"):
            self.bg_item.setVisible(True)  # возвращаем видимость

        pixmap.save(filename)
        print(f"Экспортировано: {filename}")

    def get_composite(self):
        """Объединённое изображение всех видимых слоёв"""
        result = QPixmap(self.width, self.height)
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        for layer in self.layers._layers:
            if layer.visible:
                painter.setOpacity(layer.opacity)
                painter.drawPixmap(0, 0, layer.get_preview(QSize(self.width, self.height)))
        painter.end()
        return result