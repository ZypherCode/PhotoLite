from PyQt6.QtWidgets import QVBoxLayout
from canvas import CanvasScene, CanvasView


class Document():
    """Документ объединяет сцену и вьюху, т.е. по факту вкладка"""
    def __init__(self):
        super().__init__()
        self.scene = CanvasScene()
        self.view = CanvasView(self.scene)
