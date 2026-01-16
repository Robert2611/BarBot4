"""Glass indicator control for displaying drink composition"""

from typing import List
from dataclasses import dataclass
from PyQt5 import QtWidgets, QtCore, QtGui


@dataclass
class GlasFilling:
    """Single part of a a glass filling"""

    color: str
    fraction: float


class GlasIndicator(QtWidgets.QLabel):
    """Visual representation of the ingredients inside a glas"""

    _top_width = 80
    _bottom_width = 70
    _height = 120
    _h_offset = 4
    _w_offset = 4
    _top_pos = 10
    _roundness = 10

    def __init__(self, fillings: List[GlasFilling]):
        super().__init__()
        self._fillings = fillings
        self.setMinimumSize(
            QtCore.QSize(self._top_width, self._height + 2 * self._roundness)
        )

    def _draw_filling(self, painter, start, end, draw_top=True):
        # create some support variables so the points are easier to read
        w_b = self._bottom_width
        w_t = self._top_width
        w_start = w_b + start * (w_t - w_b) - 2 * self._w_offset
        w_end = w_b + end * (w_t - w_b) - 2 * self._w_offset
        center = w_t / 2
        h = self._height - 2 * self._h_offset
        bottom = self._top_pos + self._h_offset + h * (1 - start)
        top = self._top_pos + self._h_offset + h * (1 - end)

        ### front path ##
        path = QtGui.QPainterPath()
        # bottom left
        path.moveTo(QtCore.QPointF(center - w_start / 2, +bottom))
        # bottom right
        path.quadTo(
            QtCore.QPointF(center, bottom + self._roundness),
            QtCore.QPointF(center + w_start / 2, bottom),
        )
        # top right
        path.lineTo(QtCore.QPointF(center + w_end / 2, top))
        # top left
        path.quadTo(
            QtCore.QPointF(center, top + self._roundness),
            QtCore.QPointF(center - w_end / 2, top),
        )
        # back to bottom left
        path.lineTo(QtCore.QPointF(center - w_start / 2, bottom))
        painter.drawPath(path)

        ### upper path ###
        if draw_top:
            path = QtGui.QPainterPath()
            # top left
            path.moveTo(QtCore.QPointF(center - w_end / 2, top))
            # upper bow to the right
            path.quadTo(
                QtCore.QPointF(center, top - self._roundness),
                QtCore.QPointF(center + w_end / 2, top),
            )
            # lower bow to the left
            path.quadTo(
                QtCore.QPointF(center, top + self._roundness),
                QtCore.QPointF(center - w_end / 2, top),
            )
            painter.drawPath(path)

    # pylint: disable=locally-disabled, invalid-name, missing-function-docstring
    def paintEvent(self, _):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        self._draw_glas(painter)

        sum_of_fractions = 0
        for filling in self._fillings:
            # transparent pen
            painter.setPen(QtGui.QColor("#FF999999"))
            painter.setBrush(QtGui.QColor(filling.color))
            self._draw_filling(
                painter, sum_of_fractions, sum_of_fractions + filling.fraction
            )
            sum_of_fractions += filling.fraction
        painter.end()

    def _draw_glas(self, painter):
        painter.setPen(QtGui.QColor("#FF999999"))
        painter.setBrush(QtGui.QColor("#55FFFFFF"))

        path = QtGui.QPainterPath()
        # bottom left
        path.moveTo(
            QtCore.QPointF(
                (self._top_width - self._bottom_width) / 2, self._top_pos + self._height
            )
        )
        # bottom right
        path.quadTo(
            QtCore.QPointF(
                self._top_width / 2, self._top_pos + self._height + self._roundness
            ),
            QtCore.QPointF(
                (self._top_width + self._bottom_width) / 2, self._top_pos + self._height
            ),
        )
        # top right
        path.lineTo(QtCore.QPointF(self._top_width, self._top_pos + 0))
        # top left
        path.quadTo(
            QtCore.QPointF(self._top_width / 2, self._top_pos + self._roundness),
            QtCore.QPointF(0, self._top_pos),
        )
        # back to bottom left
        path.lineTo(
            QtCore.QPointF(
                (self._top_width - self._bottom_width) / 2, self._top_pos + self._height
            )
        )
        painter.drawPath(path)

        ### top of the glas ###
        path = QtGui.QPainterPath()
        # move to left
        path.moveTo(QtCore.QPointF(0, self._top_pos))
        # upper bow to the right
        path.quadTo(
            QtCore.QPointF(self._top_width / 2, self._top_pos - self._roundness),
            QtCore.QPointF(self._top_width, self._top_pos),
        )
        # lower bow to the left
        path.quadTo(
            QtCore.QPointF(self._top_width / 2, self._top_pos + self._roundness),
            QtCore.QPointF(0, self._top_pos),
        )
        painter.drawPath(path)
