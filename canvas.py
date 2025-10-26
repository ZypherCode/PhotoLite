from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsTextItem


from PyQt6.QtGui import QFont, QBrush
from PyQt6.QtCore import Qt

class CanvasScene(QGraphicsScene):
    """Сцена хранит графические элементы (текст, изображения, слои и т.д.)"""
    def __init__(self):
        super().__init__()
        self.init_scene()

    def init_scene(self):
        # Пример содержимого — текст
        text = QGraphicsTextItem("Hello, PyQt6!")
        text.setFont(QFont("Arial", 20))
        text.setDefaultTextColor(Qt.GlobalColor.white)
        text.setPos(50, 50)
        self.addItem(text)


class CanvasView(QGraphicsView):
    """Отображает сцену, управляет масштабом, панорамой и т.д."""
    def __init__(self, scene: QGraphicsScene):
        super().__init__(scene)
        #self.setRenderHint(self.setRenderHint(hint=self.))
        self.setBackgroundBrush(QBrush(Qt.GlobalColor.darkGray))
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)