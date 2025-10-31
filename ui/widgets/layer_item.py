from PyQt6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QListWidget, QLineEdit
from PyQt6.QtCore import pyqtSignal


class LayerItem(QWidget):
    toggled = pyqtSignal(QWidget, bool)  # имя слоя + состояние
    nameChanged = pyqtSignal(QWidget, str)
    settingsOpened = pyqtSignal(QWidget)

    def __init__(self, name, visible, locked):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("background: none;")
        self.checkbox.setChecked(visible)
        self.checkbox.setObjectName("checkBoxVisible")
        self.label = QLabel(name)
        self.label.setStyleSheet("background: none;")
        self.label.setMouseTracking(True)
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.name = name

        self.lock = QLabel("Locked")
        self.lock.setStyleSheet("background: none;")
        self.layout.addWidget(self.lock)
        if locked:
            self.label.setStyleSheet("background: none; font-style: italic;")
        else:
            self.lock.hide()

        self.checkbox.toggled.connect(self.on_toggled)
        self.label.installEventFilter(self) 

        # --- Перехватываем двойной клик по label ---
    def eventFilter(self, source, event):
        if source == self.label and event.type() == event.MouseButtonDblClick and self.name != "Background":
            self.start_editing()
            return True
        return super().eventFilter(source, event)

    # --- При даблклике по телу виджета ---
    def mouseDoubleClickEvent(self, event):
        # Если клик был не по лейблу, а где-то ещё
        if not self.label.geometry().contains(event.pos()):
            self.settingsOpened.emit(self)
        super().mouseDoubleClickEvent(event)

    def on_toggled(self, state):
        self.toggled.emit(self, state)

    # --- Начинаем редактировать имя ---
    def start_editing(self):

        self.lineEdit = QLineEdit(self.label.text(), self)
        print(self.lineEdit)
        self.layout.insertWidget(1, self.lineEdit)
        self.label.hide()

        self.lineEdit.setFocus()
        self.lineEdit.selectAll()

        # Сигналы для окончания редактирования
        self.lineEdit.returnPressed.connect(self.finish_editing)
        self.lineEdit.editingFinished.connect(self.finish_editing)

    # --- Завершаем редактирование ---
    def finish_editing(self):
        if not self.lineEdit:
            return

        new_name = self.lineEdit.text().strip()
        old_name = self.label.text()
        self.label.setText(new_name)
        self.label.show()

        self.lineEdit.deleteLater()
        self.lineEdit = None

        if new_name != old_name:
            self.nameChanged.emit(self, new_name)
