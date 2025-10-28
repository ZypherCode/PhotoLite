from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem, QGraphicsTextItem
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtGui import QBrush, QPen
from PyQt6.QtCore import Qt


class Layer:
    """Один слой (группа объектов на сцене)"""
    def __init__(self, name, scene, bgcolor=Qt.GlobalColor.white, width=1920, height=1080, z_value=0):
        self.name = name
        self.visible = True
        self.locked = False
        self.opacity = 1.0
        self.scene = scene
        self.type = "Layer"

        # Создаём группу, добавляем её на сцену
        self.group = QGraphicsItemGroup()
        self.group.setZValue(z_value)
        self.scene.addItem(self.group)

    # === Методы управления ===
    def delete(self):
        self.scene.removeItem(self.group)
        
    def set_scale(self, scale):
        self.group.setScale(scale)
        self.scale = scale * 100

    def set_name(self, name):
        self.name = name

    def set_z(self, z_value):
        self.group.setZValue(z_value)

    def set_visible(self, state: bool):
        """Показать/скрыть слой"""
        self.visible = state
        self.group.setVisible(state)

    def set_opacity(self, value: float):
        """Изменить прозрачность слоя (0.0–1.0)"""
        self.opacity = value
        self.group.setOpacity(value)

    def set_locked(self, state: bool):
        """Заблокировать или разблокировать слой (отключает интерактивность)"""
        self.locked = state
        self.group.setFlag(self.group.GraphicsItemFlag.ItemIsSelectable, not state)
        self.group.setFlag(self.group.GraphicsItemFlag.ItemIsMovable, not state)

    def add_item(self, item):
        """Добавить объект на слой"""
        self.scene.addItem(item)
        self.group.addToGroup(item)

    def remove_item(self, item):
        """Удалить объект со слоя"""
        self.group.removeFromGroup(item)
        self.scene.removeItem(item)

class Solid(Layer):
    def __init__(self, name, scene, bgcolor=Qt.GlobalColor.white, width=1920, height=1080, z_value=0):
        super().__init__(name, scene, bgcolor, width, height, z_value)

        self.width = width
        self.height = height
        self.scale = 1.0
        self.type = "Solid"

        # Добавляем фоновый прямоугольник
        rect_item = QGraphicsRectItem(0, 0, self.width, self.height)
        rect_item.setBrush(QBrush(bgcolor))
        rect_item.setPen(QPen(Qt.GlobalColor.black, 1))
        rect_item.setZValue(100000)  # чтобы фон был под всем остальным
        self.add_item(rect_item)

class Image(Layer):
    def __init__(self, name, scene, pixmap, width=1920, height=1080, z_value=0):
        super().__init__(name, scene, None, width, height, z_value)

        self.scale = 100
        self.type = "Image"

        item = QGraphicsPixmapItem(pixmap)
        item.setFlags(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
                    QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable)
        self.add_item(item)

class Text(Layer):
    def __init__(self, name, scene, color=Qt.GlobalColor.black, text="Lorem impsum", z_value=0):
        super().__init__(name, scene, z_value=z_value)

        self.scale = 100
        self.type = "Text"
        self.text = text

        self.item = QGraphicsTextItem(self.text)
        self.item.setFlags(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
                    QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable)
        self.add_item(self.item)

    def set_text(self, text):
        self.text = text
        self.item.setPlainText(self.text)

    def set_font(self, font):
        self.font = font
        self.item.setFont(self.font)

class LayerManager:
    """Управляет всеми слоями документа"""
    def __init__(self, scene):
        self.scene = scene
        self._layers = []
        self.active_layer = None

    def add_layer(self, name=None, layer: Layer=None):
        if not layer:
            layer = Layer(name, self.scene)
        layer.set_z(len(self._layers))
        self._layers.append(layer)
        self.active_layer = layer
        return layer

    def list_layers(self):
        return [layer.name for layer in reversed(self._layers)]  # сверху вниз

    def get_active_layer(self):
        return self.active_layer
    
    def remove(self, index):
        self._layers[index].delete()
        print(self._layers.pop(index))

    def move(self, index, direction):
        if direction:
            vector = -1
        else:
            vector = 1

        self._layers[index-vector], self._layers[index] = self._layers[index], self._layers[index-vector]

        for i, layer in enumerate(self._layers):
            layer.set_z(i)
