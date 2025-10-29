from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent, QPainter, QBrush, QColor


class CanvasView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#252525")))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._zoom_factor = 1.15  # коэффициент масштабирования
        self._current_zoom = 1.0  # текущий масштаб

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


class CanvasScene(QGraphicsScene):
    def __init__(self):
        super().__init__()