from typing import List, Any, Callable
from PyQt5 import QtWidgets, QtCore, Qt
from .common import set_no_spacing, InputMethod, move_widget_to_bottom_of_screen

class ListSelector(QtWidgets.QWidget):
    """A custom dropdown-like selector that opens as a full-width overlay at the bottom of the screen.
    This bypasses coordinate misalignment issues with standard QComboBox popups on Wayland.
    """
    on_item_selected = QtCore.pyqtSignal(object)

    def __init__(self, items: List[tuple[str, Any]], style: str = None, reference_widget: QtWidgets.QWidget = None):
        super().__init__()
        self._reference_widget = reference_widget
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setProperty("class", "Keyboard")
        if style:
            self.setStyleSheet(style)
        
        # Disable cursor if on Raspberry Pi
        # (This is usually handled by core.py for the MainWindow, 
        # but Keyboard/Numpad also set it)
        self.setCursor(QtCore.Qt.BlankCursor)

        layout = QtWidgets.QVBoxLayout()
        set_no_spacing(layout)
        self.setLayout(layout)

        # Scroll area for many items
        scroll = QtWidgets.QScrollArea()
        scroll.setProperty("class", "ContentScroller")
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Tune scroller for touch
        scroller = QtWidgets.QScroller.scroller(scroll.viewport())
        QtWidgets.QScroller.grabGesture(
            scroll.viewport(),
            QtWidgets.QScroller.LeftMouseButtonGesture
        )
        # Make it less sensitive to movement to avoid accidental scroll instead of click
        props = scroller.scrollerProperties()
        # Minimum distance to start scrolling (meters)
        # Increase to avoid micro-drags being seen as scrolls
        props.setScrollMetric(QtWidgets.QScrollerProperties.DragStartDistance, 0.05)
        # Ensure clicks are passed through immediately
        props.setScrollMetric(QtWidgets.QScrollerProperties.MousePressEventDelay, 0)
        scroller.setScrollerProperties(props)
        
        scroll_content = QtWidgets.QWidget()
        scroll_content.setProperty("class", "IdleContent")
        scroll_layout = QtWidgets.QGridLayout()
        # Larger spacing for touch
        scroll_layout.setSpacing(5) 
        scroll_content.setLayout(scroll_layout)
        
        for i, (text, data) in enumerate(items):
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(lambda _, d=data: self._handle_selection(d))
            # 2 columns
            scroll_layout.addWidget(btn, i // 2, i % 2)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Close/Cancel button
        cancel_btn = QtWidgets.QPushButton("Abbrechen")
        cancel_btn.setProperty("class", "CancelButton")
        cancel_btn.clicked.connect(self.close)
        layout.addWidget(cancel_btn)

        # Enforce height limits before positioning
        if reference_widget:
            max_h = reference_widget.height() // 2
        else:
            max_h = 400
        self.setMaximumHeight(max(max_h, 300))
        self.setFixedWidth(reference_widget.width() if reference_widget else 480)
        
        # Ensure the widget is resized according to its constraints
        self.adjustSize()

        # Position it
        move_widget_to_bottom_of_screen(self, reference_widget)

    def mousePressEvent(self, event):
        # Consume mouse press events to prevent them from reaching the MainWindow,
        # which would close the selector if it's considered "outside"
        event.accept()

    def eventFilter(self, source, event):
        # Block mouse/touch events on the selector itself from reaching MainWindow,
        # but don't intercept events on the viewport or children which would break clicking
        if event.type() in [QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseMove]:
            if source is self:
                event.accept()
                return True
        return super().eventFilter(source, event)

    def _handle_selection(self, data):
        self.on_item_selected.emit(data)
        self.close()

class SelectorButton(QtWidgets.QPushButton):
    """A button that looks like a QComboBox and opens a ListSelector when clicked."""
    selection_changed = QtCore.pyqtSignal(object)
    # alias for compatibility with QComboBox
    currentIndexChanged = QtCore.pyqtSignal(object)
    request_selection_trigger = QtCore.pyqtSignal(object, object) # target, method

    def __init__(self, text: str, items_provider: Callable[[], List[tuple[str, Any]]], style: str = None, initial_data: Any = None):
        super().__init__(text)
        self._items_provider = items_provider
        self._style = style
        self._current_data = initial_data
        self.clicked.connect(self._request_selection)
        self.setProperty("class", "SelectorButton")

    def _request_selection(self):
        self.request_selection_trigger.emit(self, InputMethod.LIST)

    def get_items(self):
        return self._items_provider()

    def handle_selection(self, data):
        self._current_data = data
        self.selection_changed.emit(data)
        self.currentIndexChanged.emit(data)
        # Update button text to reflect selection if possible
        # We find the label in the items
        items = self._items_provider()
        for text, d in items:
            if d == data:
                self.setText(text)
                break

    def currentData(self):
        return self._current_data

    def setCurrentIndex(self, index):
        items = self._items_provider()
        if 0 <= index < len(items):
            self.handle_selection(items[index][1])
