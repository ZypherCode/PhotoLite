"""
Объект сцены.
Обработка мыши
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent, QPainter, QBrush, QColor, QPen, QCursor, QPixmap


class CanvasView(QGraphicsView):
    def __init__(self, scene, doc):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#252525")))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)

        self._zoom_factor = 1.15  # коэффициент масштабирования
        self._current_zoom = 1.0  # текущий масштаб
        self.doc = doc
        self.drawing = False

        self.brush_preview = QGraphicsEllipseItem()
        self.brush_preview.setPen(QPen(Qt.GlobalColor.darkGray, 2, Qt.PenStyle.DashLine))
        self.brush_preview.setZValue(1500)
        doc.scene.addItem(self.brush_preview)

        self.cursor_default = QCursor(QPixmap("ui\\icons\\cross.svg").scaledToHeight(18), -8, -8)


    def wheelEvent(self, event):
        """Scaling by Ctrl+Alt+Wheel"""
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier and modifiers & Qt.KeyboardModifier.AltModifier:
            delta = event.angleDelta().x()
            if delta > 0:
                self.scale(self._zoom_factor, self._zoom_factor)
                self._current_zoom *= self._zoom_factor
            elif delta < 0:
                self.scale(1 / self._zoom_factor, 1 / self._zoom_factor)
                self._current_zoom /= self._zoom_factor
        else:
            super().wheelEvent(event)

    def drag(self, isDrag):
        if isDrag:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.doc.active_layer:
            self.drawing = True
            self.last_pos = self.mapToScene(event.pos()).toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not hasattr(self.doc.activeTool, "type"):
            return
        if self.doc.active_layer.type == "Image" and self.doc.activeTool.type == "Brush":
            self.setCursor(self.cursor_default)
            color = self.doc.color
            pos = self.mapToScene(event.pos()).toPoint()
            width = self.doc.brush.width
            r = width / 2
            self.brush_preview.setRect(pos.x() - width, pos.y() - width, width*2, width*2)
            self.brush_preview.show()
            if width <= 20:
                self.brush_preview.setPen(QPen(Qt.GlobalColor.darkGray, 1, Qt.PenStyle.DashLine))
            elif width <= 3:
                self.brush_preview.hide()
            else:
                self.brush_preview.setPen(QPen(Qt.GlobalColor.darkGray, 2, Qt.PenStyle.DashLine))
            if self.drawing:
                self.doc.active_layer.draw_line(self.last_pos, pos, color, width=self.doc.brush.width, erase=self.doc.erasier, hardness=self.doc.brush.hardness)
                self.last_pos = pos  # продолжение линии без перерисовки
        elif self.doc.activeTool.type == "Editor":
            super().mouseMoveEvent(event)
            self.brush_preview.hide()
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        elif self.doc.activeTool.type == "Hand":
            super().mouseMoveEvent(event)
            self.brush_preview.hide()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
        super().mouseReleaseEvent(event)


class CanvasScene(QGraphicsScene):
    def __init__(self):
        super().__init__()