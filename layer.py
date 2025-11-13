import math

from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem, QGraphicsTextItem, QGraphicsPixmapItem
from PyQt6.QtGui import QBrush, QPen, QPainter, QColor, QFont, QRadialGradient, QPixmap, QImage
from PyQt6.QtCore import Qt, QSize


class Layer:
    """Один слой (группа объектов на сцене)"""
    def __init__(self, name, scene, bgcolor=Qt.GlobalColor.white, width=1920, height=1080, z_value=0):
        self.name = name
        self.visible = True
        self.locked = False
        self.opacity = 1.0
        self.scene = scene
        self.type = "Layer"
        self.z_value = z_value
        self.scale = 100

        # Создаём группу, добавляем её на сцену
        self.group = QGraphicsItemGroup()
        self.group.setZValue(z_value)
        self.scene.addItem(self.group)

    # === Методы управления ===
    def delete(self):
        self.scene.removeItem(self.group)

    def pos(self):
        return self.group.pos()
        
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

    def get_preview(self, size: QSize = QSize(64, 64)) -> QPixmap:
        """Создает миниатюру слоя в виде QPixmap (для списка слоев)."""
        preview = QPixmap(size)
        preview.fill(Qt.GlobalColor.transparent)

        painter = QPainter(preview)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Шахматный фон (для прозрачных областей)
        cell = 8
        for y in range(0, size.height(), cell):
            for x in range(0, size.width(), cell):
                color = QColor(200, 200, 200) if (x // cell + y // cell) % 2 == 0 else QColor(240, 240, 240)
                painter.fillRect(x, y, cell, cell, color)

        # Если слой невидим - делаем полупрозрачный
        if not self.visible:
            painter.setOpacity(0.3)
        else:
            painter.setOpacity(self.opacity)

        # --- Тип слоя: Solid ---
        if self.type == "Solid":
            painter.fillRect(preview.rect(), self.solid_color)

        # --- Тип слоя: Image ---
        elif self.type == "Image" and self.pixmap:
            scaled = self.pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            x = (size.width() - scaled.width()) // 2
            y = (size.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        # --- Тип слоя: Text ---
        elif self.type == "Text" and self.text:
            painter.end()
            return QPixmap("ui\\icons\\text.svg").scaledToHeight(size.height() - 10)

        painter.end()
        return preview

class Solid(Layer):
    def __init__(self, name, scene, bgcolor=Qt.GlobalColor.white, width=1920, height=1080, z_value=0):
        super().__init__(name, scene, bgcolor, width, height, z_value)

        self.width = width
        self.height = height
        self.type = "Solid"
        self.solid_color = QColor(bgcolor)

        # Добавляем фоновый прямоугольник
        rect_item = QGraphicsRectItem(0, 0, self.width, self.height)
        rect_item.setBrush(QBrush(bgcolor))
        rect_item.setPen(QPen(Qt.GlobalColor.black, 1))
        rect_item.setZValue(100000)  # чтобы фон был под всем остальным
        self.add_item(rect_item)

from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt


class Image(Layer):
    def __init__(self, name, scene, pixmap, width=1920, height=1080, z_value=1):
        super().__init__(name, scene, None, width, height, z_value)
        self.type = "Image"
        self.pixmap = pixmap

        print(self.pixmap.hasAlphaChannel())
        img = self.pixmap.toImage()
        if img.format() != QImage.Format.Format_RGBA64:
            img = img.convertToFormat(QImage.Format.Format_RGBA64)
            self.pixmap = QPixmap.fromImage(img)
        print(img.format() == QImage.Format.Format_RGBA64)

        self.item = QGraphicsPixmapItem(self.pixmap)
        self.item.setFlags(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
                           QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable)
        self.add_item(self.item)

    def draw_line(self, p1, p2, color: QColor, width=20, erase=False, hardness=0, start_alpha=255):
        """Плавное рисование кистью или ластиком с регулируемой жёсткостью и альфой."""
        if self.locked:
            return

        # Подготовка цвета
        r, g, b = color.red(), color.green(), color.blue()
        h = hardness / 100.0
        a0 = start_alpha
        a1 = int(a0 * h)  # альфа на краю

        # Создание радиального градиента
        gradient = QRadialGradient(width, width, width)
        if erase:
            gradient.setColorAt(0.0, QColor(0, 0, 0, a0))
            gradient.setColorAt(h,   QColor(0, 0, 0, a0))
            gradient.setColorAt(1.0, QColor(0, 0, 0, a1))
        else:
            gradient.setColorAt(0.0, QColor(r, g, b, a0))
            gradient.setColorAt(h,   QColor(r, g, b, a0))
            gradient.setColorAt(1.0, QColor(r, g, b, a1))

        brush = QBrush(gradient)

        # Настраиваем painter
        painter = QPainter(self.pixmap)
        #painter.setOpacity(start_alpha / 255)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        if erase:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        else:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # Расстояние между точками
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        steps = int(dist / 100) + 1

        # Рисуем плавно
        for i in range(steps):
            t = i / steps
            x = p1.x() + dx * t - self.pos().x()
            y = p1.y() + dy * t - self.pos().y()
            painter.save()
            painter.translate(x - width, y - width)
            painter.setBrush(brush)
            painter.drawEllipse(0, 0, width * 2, width * 2)
            painter.restore()

        painter.end()

        if self.item:
            self.item.setPixmap(self.pixmap)

class Text(Layer):
    def __init__(self, name, scene, color=QColor(0, 0, 0), text="Lorem ipsum", z_value=0):
        super().__init__(name, scene, z_value=z_value)

        self.scale = 100
        self.type = "Text"
        self.text = text
        self.font = QFont("Arial")
        self.font.setPixelSize(150)
        self.text_color = QColor(color)

        self.item = QGraphicsTextItem(self.text)
        self.item.setFont(self.font)
        self.item.setFlags(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
                    QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable)
        self.item.setDefaultTextColor(self.text_color)
        self.add_item(self.item)

    def set_text(self, text):
        self.text = text
        self.item.setPlainText(self.text)

    def set_font(self, font):
        self.font = font
        self.item.setFont(self.font)

    def set_color(self, color):
        self.text_color = color
        self.item.setDefaultTextColor(self.text_color)

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
        self._layers.pop(index)

    def move(self, index, direction):
        if direction:
            vector = -1
        else:
            vector = 1

        self._layers[index-vector], self._layers[index] = self._layers[index], self._layers[index-vector]

        for i, layer in enumerate(self._layers):
            layer.set_z(i)
