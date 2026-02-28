import logging
import time
from typing import List, Any, Callable
from PyQt5 import QtWidgets, QtCore, Qt
from ..common import set_no_spacing, InputMethod, move_widget_to_bottom_of_screen, is_raspberry

class ListSelector(QtWidgets.QWidget):
    """A custom dropdown-like selector that opens as a full-screen transparent overlay.
    This resolves coordinate mapping conflicts between the MainWindow and the pop-up on Wayland.
    """
    on_item_selected = QtCore.pyqtSignal(object)

    def __init__(self, items: List[tuple[str, Any]], style: str = None, reference_widget: QtWidgets.QWidget = None):
        super().__init__()
        self._reference_widget = reference_widget
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setProperty("class", "Keyboard")
        if style:
            self.setStyleSheet(style)
        
        # Disable cursor if on Raspberry Pi
        self.setCursor(QtCore.Qt.BlankCursor)
        self._open_time = time.time()

        # Full-screen vertical layout
        self._main_layout = QtWidgets.QVBoxLayout()
        set_no_spacing(self._main_layout)
        self.setLayout(self._main_layout)

        # Transparent spacer at the top (tapping here closes the selector)
        self._top_spacer = QtWidgets.QWidget()
        self._top_spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._main_layout.addWidget(self._top_spacer)

        # Content container at the bottom (the actual visible selector)
        self._content_container = QtWidgets.QWidget()
        self._content_container.setProperty("class", "Keyboard") # Ensure it gets the background color
        self._main_layout.addWidget(self._content_container)

        content_layout = QtWidgets.QVBoxLayout()
        set_no_spacing(content_layout)
        self._content_container.setLayout(content_layout)

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
        
        # Make it much less sensitive to movement to avoid accidental scroll instead of click.
        # This is critical on Raspberry Pi touchscreens which often report 
        # large coordinate "jumps" (>200px) immediately after a press.
        props = scroller.scrollerProperties()
        # Minimum distance to start scrolling in meters (~0.1m is ~400px at 96dpi)
        props.setScrollMetric(QtWidgets.QScrollerProperties.DragStartDistance, 0.1)
        # Ensure clicks are passed through immediately without delay
        props.setScrollMetric(QtWidgets.QScrollerProperties.MousePressEventDelay, 0)
        # Disable flicking/momentum to stay stable during taps
        props.setScrollMetric(QtWidgets.QScrollerProperties.MaximumVelocity, 0.01)
        scroller.setScrollerProperties(props)
        
        # Install event filter to log events for coordinate jump debugging
        scroll.viewport().installEventFilter(self)
        
        scroll_content = QtWidgets.QWidget()
        scroll_content.setProperty("class", "IdleContent")
        scroll_layout = QtWidgets.QGridLayout()
        # Larger spacing for touch
        scroll_layout.setSpacing(5) 
        scroll_content.setLayout(scroll_layout)
        
        for i, (text, data) in enumerate(items):
            btn = QtWidgets.QPushButton(text)
            # Use a wrapper to log which button was clicked
            def on_click(checked, d=data, t=text):
                logging.debug(f"ListSelector: Button clicked: '{t}'")
                self._handle_selection(d)
            btn.clicked.connect(on_click)
            # 2 columns
            scroll_layout.addWidget(btn, i // 2, i % 2)
        
        scroll.setWidget(scroll_content)
        content_layout.addWidget(scroll)

        # Close/Cancel button
        cancel_btn = QtWidgets.QPushButton("Abbrechen")
        cancel_btn.setProperty("class", "CancelButton")
        cancel_btn.clicked.connect(self.close)
        content_layout.addWidget(cancel_btn)

        # Enforce height limits for the content container
        if reference_widget:
            max_h = reference_widget.height() // 2
        else:
            max_h = 400
        self._content_container.setMaximumHeight(max(max_h, 300))
        # Overlay is full width anyway, but content container should match expectations
        self._content_container.setFixedWidth(reference_widget.width() if reference_widget else 480)

    def mousePressEvent(self, event):
        # Log to track the jump
        logging.debug(f"ListSelector: mousePressEvent at {event.pos()} (global: {event.globalPos()})")
        
        # If tapping outside the content but inside the overlay, close it.
        # But only after a short delay to avoid accidental closes during the jump.
        if time.time() - self._open_time > 0.5:
            if not self._content_container.geometry().contains(event.pos()):
                logging.debug("ListSelector: Clicked outside content, closing.")
                self.close()
        event.accept()

    def eventFilter(self, source, event):
        # Log events on components to track the jump
        if event.type() in [QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseMove]:
            event_name = {
                QtCore.QEvent.MouseButtonPress: "Press",
                QtCore.QEvent.MouseButtonRelease: "Release",
                QtCore.QEvent.MouseMove: "Move"
            }.get(event.type())
            logging.debug(f"ListSelector: EventFilter {event_name} on {source.__class__.__name__} at {event.pos()} (global: {event.globalPos()})")
        return super().eventFilter(source, event)

    def _handle_selection(self, data):
        self.on_item_selected.emit(data)
        self.close()

    def show(self):
        if is_raspberry():
            self.showFullScreen()
        else:
            super().show()

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
