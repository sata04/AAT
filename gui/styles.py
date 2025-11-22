"""
UI Style Definitions
Defines the color palette, typography, and widget styles for the application.
"""

from enum import Enum, auto
from pathlib import Path

from PySide6.QtGui import QColor, QPalette


class ThemeType(Enum):
    DARK = auto()
    LIGHT = auto()
    SYSTEM = auto()

    @classmethod
    def from_config(cls, value) -> "ThemeType":
        """Convert a persisted config value into a ThemeType."""
        if isinstance(value, cls):
            return value

        normalized = str(value).strip().lower() if value is not None else "system"
        if normalized == "dark":
            return cls.DARK
        if normalized == "light":
            return cls.LIGHT
        return cls.SYSTEM

    def to_config_value(self) -> str:
        """Return the config-friendly string for this ThemeType."""
        if self == ThemeType.DARK:
            return "dark"
        if self == ThemeType.LIGHT:
            return "light"
        return "system"


# --- Color Palette ---
class Colors:
    # Dark Theme Colors
    DARK_BG_PRIMARY = "#111827"  # Slate 900
    DARK_BG_SECONDARY = "#1F2937"  # Slate 800
    DARK_BG_TERTIARY = "#374151"  # Slate 700
    DARK_PRIMARY = "#818CF8"  # Indigo 400
    DARK_PRIMARY_VARIANT = "#4F46E5"  # Indigo 600
    DARK_SECONDARY = "#38BDF8"  # Sky 400
    DARK_ERROR = "#F87171"  # Red 400
    DARK_TEXT_PRIMARY = "#F9FAFB"  # Gray 50
    DARK_TEXT_SECONDARY = "#9CA3AF"  # Gray 400
    DARK_TEXT_DISABLED = "#6B7280"  # Gray 500
    DARK_BORDER = "#4B5563"  # Gray 600
    DARK_BORDER_FOCUS = "#818CF8"  # Indigo 400

    # Light Theme Colors
    LIGHT_BG_PRIMARY = "#F8F9FA"
    LIGHT_BG_SECONDARY = "#FFFFFF"
    LIGHT_BG_TERTIARY = "#F1F3F4"
    LIGHT_PRIMARY = "#4F46E5"
    LIGHT_PRIMARY_VARIANT = "#4338CA"
    LIGHT_SECONDARY = "#0EA5E9"
    LIGHT_ERROR = "#B00020"
    LIGHT_TEXT_PRIMARY = "#111827"
    LIGHT_TEXT_SECONDARY = "#4B5563"
    LIGHT_TEXT_DISABLED = "#9E9E9E"
    LIGHT_BORDER = "#E5E7EB"
    LIGHT_BORDER_FOCUS = "#4F46E5"

    # Current Theme Colors (Defaults to Dark)
    BG_PRIMARY = DARK_BG_PRIMARY
    BG_SECONDARY = DARK_BG_SECONDARY
    BG_TERTIARY = DARK_BG_TERTIARY
    PRIMARY = DARK_PRIMARY
    PRIMARY_VARIANT = DARK_PRIMARY_VARIANT
    SECONDARY = DARK_SECONDARY
    ERROR = DARK_ERROR
    TEXT_PRIMARY = DARK_TEXT_PRIMARY
    TEXT_SECONDARY = DARK_TEXT_SECONDARY
    TEXT_DISABLED = DARK_TEXT_DISABLED
    BORDER = DARK_BORDER
    BORDER_FOCUS = DARK_BORDER_FOCUS

    @classmethod
    def set_theme(cls, theme_type: ThemeType):
        # If SYSTEM, resolve to actual theme
        if theme_type == ThemeType.SYSTEM:
            # This logic is slightly circular because we need QApplication to check system theme,
            # but we might be calling this before app is fully ready or from apply_theme.
            # We will handle the actual detection in apply_theme and pass the resolved type here,
            # OR we can try to detect it here if possible.
            # For simplicity, let's assume the caller resolves SYSTEM to LIGHT/DARK before calling set_theme
            # OR we default to DARK if we can't detect.
            pass

        if theme_type == ThemeType.LIGHT:
            cls.BG_PRIMARY = cls.LIGHT_BG_PRIMARY
            cls.BG_SECONDARY = cls.LIGHT_BG_SECONDARY
            cls.BG_TERTIARY = cls.LIGHT_BG_TERTIARY
            cls.PRIMARY = cls.LIGHT_PRIMARY
            cls.PRIMARY_VARIANT = cls.LIGHT_PRIMARY_VARIANT
            cls.SECONDARY = cls.LIGHT_SECONDARY
            cls.ERROR = cls.LIGHT_ERROR
            cls.TEXT_PRIMARY = cls.LIGHT_TEXT_PRIMARY
            cls.TEXT_SECONDARY = cls.LIGHT_TEXT_SECONDARY
            cls.TEXT_DISABLED = cls.LIGHT_TEXT_DISABLED
            cls.BORDER = cls.LIGHT_BORDER
            cls.BORDER_FOCUS = cls.LIGHT_BORDER_FOCUS
        else:
            # Default to Dark for DARK or fallback
            cls.BG_PRIMARY = cls.DARK_BG_PRIMARY
            cls.BG_SECONDARY = cls.DARK_BG_SECONDARY
            cls.BG_TERTIARY = cls.DARK_BG_TERTIARY
            cls.PRIMARY = cls.DARK_PRIMARY
            cls.PRIMARY_VARIANT = cls.DARK_PRIMARY_VARIANT
            cls.SECONDARY = cls.DARK_SECONDARY
            cls.ERROR = cls.DARK_ERROR
            cls.TEXT_PRIMARY = cls.DARK_TEXT_PRIMARY
            cls.TEXT_SECONDARY = cls.DARK_TEXT_SECONDARY
            cls.TEXT_DISABLED = cls.DARK_TEXT_DISABLED
            cls.BORDER = cls.DARK_BORDER
            cls.BORDER_FOCUS = cls.DARK_BORDER_FOCUS


# --- Typography ---
class Fonts:
    FAMILY_SANS = "Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    FAMILY_MONO = "Consolas, Monaco, Courier New, monospace"

    SIZE_HEADER = "20px"
    SIZE_SUBHEADER = "18px"
    SIZE_BODY = "15px"
    SIZE_SMALL = "13px"

    WEIGHT_BOLD = "600"
    WEIGHT_NORMAL = "400"


ASSETS_DIR = Path(__file__).resolve().parent / "assets"


# Toggle checkbox helpers
def get_toggle_checkbox_styles() -> str:
    """Styles that render QCheckBox indicators in a pill/toggle-like shape without external images."""
    return f"""
    /* Toggle-style Checkboxes */
    QCheckBox {{
        spacing: 12px;
        padding: 8px 0;
        color: {Colors.TEXT_PRIMARY};
    }}
    QCheckBox::indicator {{
        width: 44px;
        height: 24px;
        border-radius: 12px;
        border: 2px solid {Colors.BORDER};
        background: {Colors.BG_TERTIARY};
        margin-right: 6px;
    }}
    QCheckBox::indicator:unchecked:hover {{
        border-color: {Colors.PRIMARY};
    }}
    QCheckBox::indicator:checked {{
        border-color: {Colors.PRIMARY};
        background: {Colors.PRIMARY};
    }}
    QCheckBox::indicator:checked:disabled {{
        border-color: {Colors.TEXT_DISABLED};
        background: {Colors.TEXT_DISABLED};
    }}
    QCheckBox::indicator:unchecked:disabled {{
        border-color: {Colors.TEXT_DISABLED};
        background: {Colors.BG_TERTIARY};
    }}
    """


# --- Stylesheet ---
def get_stylesheet():
    arrow_icon_path = (ASSETS_DIR / "combo_arrow.svg").as_posix()
    # Fallback to Qt's built-in arrow if the local asset is missing
    if not Path(arrow_icon_path).exists():
        arrow_icon_path = ":/qt-project.org/styles/commonstyle/images/down-16.png"
    toggle_styles = get_toggle_checkbox_styles()

    return f"""
    /* Global Reset */
    * {{
        font-family: {Fonts.FAMILY_SANS};
        font-size: {Fonts.SIZE_BODY};
        color: {Colors.TEXT_PRIMARY};
        selection-background-color: {Colors.PRIMARY};
        selection-color: {Colors.BG_PRIMARY};
    }}

    /* QMainWindow & QWidget Defaults */
    QWidget {{
        background-color: transparent;
    }}
    QMainWindow, QDialog {{
        background-color: {Colors.BG_PRIMARY};
    }}

    /* QFrame / Containers */
    QFrame#Container, QWidget#Container {{
        background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 10px;
    }}
    QGroupBox {{
        background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 10px;
        margin-top: 1.8em;
        padding-top: 12px;
        padding-bottom: 12px;
        padding-left: 12px;
        padding-right: 12px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: {Colors.PRIMARY};
        font-weight: {Fonts.WEIGHT_BOLD};
        font-size: {Fonts.SIZE_SUBHEADER};
    }}

    /* Labels */
    QLabel {{
        color: {Colors.TEXT_PRIMARY};
        padding: 2px;
    }}
    QLabel#Header {{
        font-size: {Fonts.SIZE_HEADER};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.PRIMARY};
        padding: 4px 0;
    }}
    QLabel#SubHeader {{
        font-size: {Fonts.SIZE_SUBHEADER};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.TEXT_SECONDARY};
        padding: 2px 0;
    }}
    QLabel#Status {{
        color: {Colors.TEXT_SECONDARY};
        font-size: {Fonts.SIZE_SMALL};
    }}
    QLabel#EmptyStateTitle {{
        font-size: 22px;
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.TEXT_PRIMARY};
        margin-bottom: 8px;
    }}
    QLabel#Badge, QLabel#BadgeInfo, QLabel#BadgeAccent, QLabel#BadgeMuted {{
        border-radius: 12px;
        padding: 6px 12px;
        font-size: {Fonts.SIZE_SMALL};
        font-weight: {Fonts.WEIGHT_BOLD};
        background-color: {Colors.BG_TERTIARY};
        color: {Colors.TEXT_SECONDARY};
        border: 1px solid {Colors.BORDER};
    }}
    QLabel#BadgeInfo {{
        color: {Colors.TEXT_PRIMARY};
    }}
    QLabel#BadgeAccent {{
        background-color: {Colors.PRIMARY};
        color: {Colors.BG_PRIMARY};
        border: 1px solid {Colors.PRIMARY};
    }}
    QLabel#BadgeMuted {{
        color: {Colors.TEXT_SECONDARY};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {Colors.PRIMARY_VARIANT};
        color: #FFFFFF; /* Always white text on primary variant */
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: {Fonts.WEIGHT_BOLD};
        font-size: {Fonts.SIZE_BODY};
    }}
    QPushButton:hover {{
        background-color: {Colors.PRIMARY};
        color: #FFFFFF;
    }}
    QPushButton:pressed {{
        background-color: {Colors.SECONDARY};
    }}
    QPushButton:disabled {{
        background-color: {Colors.BG_TERTIARY};
        color: {Colors.TEXT_DISABLED};
    }}

    /* Secondary Button (Outline) */
    QPushButton#Secondary {{
        background-color: transparent;
        border: 1px solid {Colors.PRIMARY};
        color: {Colors.PRIMARY};
    }}
    QPushButton#Secondary:hover {{
        background-color: {Colors.PRIMARY};
        color: #FFFFFF;
    }}

    {toggle_styles}

    /* Inputs */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {Colors.BG_TERTIARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px 10px;
        color: {Colors.TEXT_PRIMARY};
        min-height: 24px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {Colors.BORDER_FOCUS};
    }}

    /* QComboBox - Improved Design */
    QComboBox {{
        background-color: {Colors.BG_TERTIARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px 22px 8px 12px; /* Keep arrow compact to preserve label width */
        color: {Colors.TEXT_PRIMARY};
        min-width: 6em;
        min-height: 24px;
    }}
    QComboBox:hover {{
        border-color: {Colors.PRIMARY};
    }}
    QComboBox:focus {{
        border: 1px solid {Colors.BORDER_FOCUS};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 20px;
        border: none; /* Trim wasted button space */
        background: transparent;
        margin: 0;
        padding: 0;
    }}
    /* Custom Arrow using CSS shapes or SVG */
    QComboBox::down-arrow {{
        image: url("{arrow_icon_path}");
        width: 12px;
        height: 12px;
        margin-right: 4px;
    }}
    QComboBox::down-arrow:on {{
        top: 1px;
        left: 1px;
    }}

    /* QComboBox Popup List */
    QComboBox QAbstractItemView {{
        background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER};
        selection-background-color: {Colors.PRIMARY};
        selection-color: #FFFFFF;
        outline: none;
        padding: 6px;
    }}

    /* Tables */
    QTableWidget {{
        background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER};
        gridline-color: {Colors.BORDER};
        alternate-background-color: {Colors.BG_TERTIARY};
        color: {Colors.TEXT_PRIMARY};
    }}
    QHeaderView::section {{
        background-color: {Colors.BG_TERTIARY};
        color: {Colors.TEXT_PRIMARY};
        padding: 8px;
        border: 1px solid {Colors.BORDER};
        font-weight: {Fonts.WEIGHT_BOLD};
        font-size: {Fonts.SIZE_BODY};
    }}
    QTableWidget::item {{
        padding: 4px;
    }}
    QTableWidget::item:selected {{
        background-color: {Colors.PRIMARY_VARIANT};
        color: #FFFFFF;
    }}

    /* ScrollBars */
    QScrollBar:vertical {{
        border: none;
        background: {Colors.BG_PRIMARY};
        width: 12px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {Colors.BG_TERTIARY};
        min-height: 24px;
        border-radius: 6px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        border: none;
        background: {Colors.BG_PRIMARY};
        height: 12px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {Colors.BG_TERTIARY};
        min-width: 24px;
        border-radius: 6px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ProgressBar */
    QProgressBar {{
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        text-align: center;
        background-color: {Colors.BG_TERTIARY};
        color: {Colors.TEXT_PRIMARY};
        min-height: 20px;
    }}
    QProgressBar::chunk {{
        background-color: {Colors.SECONDARY};
        border-radius: 5px;
    }}

    /* Splitter */
    QSplitter::handle {{
        background-color: {Colors.BORDER};
        width: 2px;
    }}
    """


def apply_theme(app, theme: ThemeType = ThemeType.SYSTEM):
    """Applies the specified theme to the QApplication instance."""

    # Resolve SYSTEM theme
    target_theme = theme
    if theme == ThemeType.SYSTEM:
        # Check system color scheme
        # Qt 6.5+ supports styleHints().colorScheme()
        # For older versions or if detection fails, default to Dark
        try:
            from PySide6.QtCore import Qt

            target_theme = ThemeType.LIGHT if app.styleHints().colorScheme() == Qt.ColorScheme.Light else ThemeType.DARK
        except Exception:
            target_theme = ThemeType.DARK

    Colors.set_theme(target_theme)

    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_SECONDARY))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(Colors.SECONDARY))
    palette.setColor(QPalette.ColorRole.Link, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.BG_PRIMARY))

    app.setPalette(palette)
    app.setStyleSheet(get_stylesheet())
