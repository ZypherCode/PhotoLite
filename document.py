from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsItem
from canvas import CanvasScene, CanvasView
from layer import LayerManager, Layer, Solid, Image, Text
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor
from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import QRectF


class Document(QWidget):
    def __init__(self, name="Новый документ", width=1280, height=720, bgcolor=Qt.GlobalColor.transparent):
        super().__init__()
        self.name = name
        self.width = width
        self.height = height
        self.activeTool = None

        self.color = (255, 0, 0)

        # Сцена и вью
        self.scene = CanvasScene()
        self.view = CanvasView(self.scene)
        self.scene.setSceneRect(0, 0, width, height)

        # Менеджер слоёв
        self.layers = LayerManager(self.scene)
        if bgcolor == Qt.GlobalColor.transparent:
            self.add_bg_layer()
        else:
            self.add_solid_layer("Background", color=bgcolor)
        '''lyr = Layer("Background", self.scene, Qt.GlobalColor.white, width, height)
        self.layers.add_layer(layer=lyr)'''

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        #self.export_area("part.png", QRectF(100, 100, 400, 300))
        self.add_text_layer("Text", "Lorem impsum")

    def move_layer(self, index, direction):
        index = len(self.layers._layers) - index - 1
        self.layers.move(index, direction)

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

    def lock_all(self, isMove):
        for item in self.layers._layers:
            if item.name == "Background":
                continue
            item.set_locked(isMove)

    def add_solid_layer(self, name, locked=False, color=Qt.GlobalColor.white):
        lyr = Solid(name, self.scene, color, self.width, self.height)
        lyr.set_locked(locked)
        self.layers.add_layer(layer=lyr)

    def add_pixmap_layer(self, name, pixmap):
        lyr = Image(name, self.scene, pixmap, self.width, self.height)
        lyr.set_locked(False)
        self.layers.add_layer(layer=lyr)

    def add_text_layer(self, name, text):
        lyr = Text(name, self.scene, text)
        lyr.set_locked(False)
        self.layers.add_layer(layer=lyr)

    def get_layer(self, index):
        index = len(self.layers._layers) - index - 1
        return self.layers._layers[index]

    def add_bg_layer(self):
        """Добавляет слой-фон с шахматками для прозрачности"""
        # создаём pixmap шахматного паттерна
        checker = QPixmap(20, 20)
        checker.fill(QColor("lightGray"))
        painter = QPainter(checker)
        painter.fillRect(0, 0, 10, 10, QColor("white"))
        painter.fillRect(10, 10, 10, 10, QColor("white"))
        painter.end()

        bg_brush = QBrush(checker)
        rect_item = QGraphicsRectItem(self.scene.sceneRect())
        rect_item.setBrush(bg_brush)
        rect_item.setZValue(-1)  # всегда самый низ
        self.scene.addItem(rect_item)

        # создаём слой для совместимости с остальными слоями
        bg_layer = Layer("Background", self.scene, Qt.GlobalColor.transparent, self.width, self.height)
        bg_layer.group.addToGroup(rect_item)
        self.layers.add_layer(layer=bg_layer)  # ставим первым слоем
        self.bg_item = rect_item  # храним ссылку, чтобы скрывать при экспорте

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
