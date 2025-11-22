"""
Custom GUI Widgets
"""

from PySide6.QtCore import (
    Property,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QCheckBox,
)

from gui.styles import Colors


class ToggleSwitch(QCheckBox):
    """
    A modern toggle switch widget that replaces the standard QCheckBox.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Configure widget
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Animation setup
        self._position = 0.0
        self._animation = QPropertyAnimation(self, b"position")
        self._animation.setDuration(200)  # ms

        # Connect state change to animation
        self.stateChanged.connect(self._start_animation)

    @Property(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def _start_animation(self, state):
        self._animation.stop()
        if state:
            self._animation.setEndValue(1.0)
        else:
            self._animation.setEndValue(0.0)
        self._animation.start()

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensions
        toggle_width = 40
        toggle_height = 24
        radius = toggle_height / 2
        text_gap = 8

        # Draw track
        track_rect = QRectF(0, (self.height() - toggle_height) / 2, toggle_width, toggle_height)
        track_path = QPainterPath()
        track_path.addRoundedRect(track_rect, radius, radius)

        # Determine colors based on state
        if self.isChecked():
            track_color = QColor(Colors.PRIMARY)
            thumb_color = QColor(
                Colors.BG_PRIMARY
            )  # White/Black depending on theme, but usually white looks best on colored track
            if Colors.BG_PRIMARY == Colors.LIGHT_BG_PRIMARY:  # If light mode
                thumb_color = QColor("#FFFFFF")
            border_color = QColor(Colors.PRIMARY)
        else:
            track_color = QColor(Colors.BG_TERTIARY)
            thumb_color = QColor(Colors.TEXT_SECONDARY)
            border_color = QColor(Colors.BORDER)

        painter.setPen(border_color)
        painter.setBrush(track_color)
        painter.drawPath(track_path)

        # Draw thumb
        thumb_radius = 10
        # Interpolate position
        # 0.0 -> left (unchecked), 1.0 -> right (checked)
        # Margin from edges
        margin = 3
        start_x = margin + thumb_radius
        end_x = toggle_width - margin - thumb_radius
        current_x = start_x + (end_x - start_x) * self._position

        thumb_center_y = self.height() / 2

        painter.setBrush(thumb_color)
        painter.drawEllipse(
            QRectF(current_x - thumb_radius, thumb_center_y - thumb_radius, thumb_radius * 2, thumb_radius * 2)
        )

        # Draw text if provided
        if self.text():
            painter.setPen(QColor(Colors.TEXT_PRIMARY if self.isEnabled() else Colors.TEXT_DISABLED))
            text_rect = QRectF(
                track_rect.right() + text_gap, 0, self.width() - track_rect.right() - text_gap, self.height()
            )
            painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), self.text())

        painter.end()

    def sizeHint(self):
        if not self.text():
            return QSize(44, 26)
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(self.text())
        height = max(metrics.height(), 26)
        return QSize(44 + 8 + text_width, height)
