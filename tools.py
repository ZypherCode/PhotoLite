"""
Инструменты
Кисть и ластик в данном контексте - одно и тоже
"""

class BasicTool:
    pass


class Hand(BasicTool):
    def __init__(self):
        super().__init__()
        self.type = "Hand"


class Editor(BasicTool):
    def __init__(self):
        super().__init__()
        self.type = "Editor"


class BrushTool(BasicTool):
    def __init__(self):
        super().__init__()
        self.type = "Brush"
        self.width = 4
        self.hardness = 0