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