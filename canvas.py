from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent, QPainter, QBrush, QColor


class CanvasView(QGraphicsView):
    def __init__(self, scene, doc):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#252525")))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._zoom_factor = 1.15  # коэффициент масштабирования
        self._current_zoom = 1.0  # текущий масштаб
        self.doc = doc

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
        if self.drawing and self.doc.active_layer.type == "Image" and self.doc.activeTool.type == "Brush":
            color = self.doc.color
            pos = self.mapToScene(event.pos()).toPoint()
            self.doc.active_layer.draw_line(self.last_pos, pos, color, width=self.doc.brush.width, erase=self.doc.erasier)
            self.last_pos = pos  # продолжение линии без перерисовки
        elif self.doc.activeTool.type == "Editor":
            super().mouseMoveEvent(event)
        elif self.doc.activeTool.type == "Hand":
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
        super().mouseReleaseEvent(event)


class CanvasScene(QGraphicsScene):
    def __init__(self):
        super().__init__()