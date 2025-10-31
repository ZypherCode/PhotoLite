from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt

class MyBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.setFixedHeight(32)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            background-color: #2b2b2b;
            color: #f0f0f0;
            border-bottom: 1px solid #444;
        """)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 0, 8, 0)
        self.layout.setSpacing(6)

        # Название окна
        self.title = QLabel("Pl")
        self.title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.title)
        self.layout.addStretch()

        # Кнопка свернуть
        btn_min = QPushButton("—")
        btn_min.setFixedSize(24, 24)
        btn_min.clicked.connect(lambda: self.parent.showMinimized())
        self.layout.addWidget(btn_min)

        # Кнопка развернуть / восстановить
        self.btn_max = QPushButton("☐")
        self.btn_max.setFixedSize(24, 24)
        self.btn_max.clicked.connect(self.toggle_max_restore)
        self.layout.addWidget(self.btn_max)

        # Кнопка закрыть
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.clicked.connect(lambda: self.parent.close())
        self.layout.addWidget(btn_close)

        # Внутри MyBar.__init__
        self.menu_bar = parent.menubar
        self.menu_bar.setStyleSheet("background: transparent; color: white;")
        self.menu_bar.setFixedHeight(24)  # по вкусу

        # Добавляем в layout — допустим, между title и кнопками
        self.layout.insertWidget(1, self.menu_bar)


        # Минималистичный стиль кнопок
        for btn in (btn_min, self.btn_max, btn_close):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #f0f0f0;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #444;
                }
                QPushButton:pressed {
                    background-color: #555;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.parent:
            diff = event.globalPosition().toPoint() - self.drag_pos
            self.parent.move(self.parent.pos() + diff)
            self.drag_pos = event.globalPosition().toPoint()
        event.accept()

    def toggle_max_restore(self):
        """Разворачивает/восстанавливает окно"""
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.btn_max.setText("☐")
        else:
            self.parent.showMaximized()
            self.btn_max.setText("🗗")
