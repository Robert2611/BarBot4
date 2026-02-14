from typing import List, Any, Callable
from PyQt5 import QtWidgets, QtCore, Qt
from .common import set_no_spacing

class ListSelector(QtWidgets.QWidget):
    """A custom dropdown-like selector that opens as a full-width overlay at the bottom of the screen.
    This bypasses coordinate misalignment issues with standard QComboBox popups on Wayland.
    """
    on_item_selected = QtCore.pyqtSignal(object)

    def __init__(self, items: List[tuple[str, Any]], style: str = None):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setProperty("class", "ListSelector")
        if style:
            self.setStyleSheet(style)
        
        layout = QtWidgets.QVBoxLayout()
        set_no_spacing(layout)
        self.setLayout(layout)

        # Scroll area for many items
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout()
        # Larger spacing for touch
        scroll_layout.setSpacing(5) 
        scroll_content.setLayout(scroll_layout)
        
        for text, data in items:
            btn = QtWidgets.QPushButton(text)
            btn.setMinimumHeight(60) # Large hit target
            btn.clicked.connect(lambda _, d=data: self._handle_selection(d))
            scroll_layout.addWidget(btn)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Close/Cancel button
        cancel_btn = QtWidgets.QPushButton("Abbrechen")
        cancel_btn.setMinimumHeight(60)
        cancel_btn.setProperty("class", "CancelButton")
        cancel_btn.clicked.connect(self.close)
        layout.addWidget(cancel_btn)

        # Position it
        self._position_on_screen()

    def _position_on_screen(self):
        desktop = QtWidgets.QApplication.desktop().availableGeometry()
        width = desktop.width()
        height = min(desktop.height() // 2, 400) # Max half screen or 400px
        self.setGeometry(0, desktop.height() - height, width, height)

    def _handle_selection(self, data):
        self.on_item_selected.emit(data)
        self.close()

class SelectorButton(QtWidgets.QPushButton):
    """A button that looks like a QComboBox and opens a ListSelector when clicked."""
    selection_changed = QtCore.pyqtSignal(object)

    def __init__(self, text: str, items_provider: Callable[[], List[tuple[str, Any]]], style: str = None):
        super().__init__(text)
        self._items_provider = items_provider
        self._style = style
        self.clicked.connect(self._open_selector)
        self.setProperty("class", "SelectorButton")

    def _open_selector(self):
        items = self._items_provider()
        self._selector = ListSelector(items, self._style)
        self._selector.on_item_selected.connect(self._handle_selection)
        self._selector.show()

    def _handle_selection(self, data):
        self.selection_changed.emit(data)
        # Update button text to reflect selection if possible
        # We find the label in the items
        items = self._items_provider()
        for text, d in items:
            if d == data:
                self.setText(text)
                break
