"""Tests for gui/styles.py — ThemeType enum and apply_theme behaviour."""

import pytest

from gui.styles import Colors, ThemeType, apply_theme

# --- ThemeType.from_config ---


def test_theme_type_from_config_dark():
    assert ThemeType.from_config("dark") == ThemeType.DARK


def test_theme_type_from_config_light():
    assert ThemeType.from_config("light") == ThemeType.LIGHT


def test_theme_type_from_config_system():
    assert ThemeType.from_config("system") == ThemeType.SYSTEM


def test_theme_type_from_config_none():
    assert ThemeType.from_config(None) == ThemeType.SYSTEM


def test_theme_type_from_config_case_insensitive():
    assert ThemeType.from_config("DARK") == ThemeType.DARK
    assert ThemeType.from_config("Light") == ThemeType.LIGHT


def test_theme_type_from_config_with_spaces():
    assert ThemeType.from_config("  dark  ") == ThemeType.DARK


def test_theme_type_from_config_unknown_returns_system():
    assert ThemeType.from_config("unknown") == ThemeType.SYSTEM


def test_theme_type_from_config_identity():
    """Passing a ThemeType enum directly should return itself."""
    assert ThemeType.from_config(ThemeType.DARK) == ThemeType.DARK
    assert ThemeType.from_config(ThemeType.LIGHT) == ThemeType.LIGHT
    assert ThemeType.from_config(ThemeType.SYSTEM) == ThemeType.SYSTEM


# --- ThemeType.to_config_value ---


def test_theme_type_to_config_value():
    assert ThemeType.DARK.to_config_value() == "dark"
    assert ThemeType.LIGHT.to_config_value() == "light"
    assert ThemeType.SYSTEM.to_config_value() == "system"


def test_theme_type_roundtrip():
    """from_config(to_config_value()) should be an identity for every variant."""
    for theme in ThemeType:
        assert ThemeType.from_config(theme.to_config_value()) == theme


# --- apply_theme / Colors mutation ---


@pytest.mark.gui
def test_apply_theme_dark_sets_colors(qapp):
    apply_theme(qapp, ThemeType.DARK)
    assert Colors.BG_PRIMARY == Colors.DARK_BG_PRIMARY
    assert Colors.TEXT_PRIMARY == Colors.DARK_TEXT_PRIMARY
    assert Colors.PRIMARY == Colors.DARK_PRIMARY
    assert Colors.BORDER == Colors.DARK_BORDER


@pytest.mark.gui
def test_apply_theme_light_sets_colors(qapp):
    apply_theme(qapp, ThemeType.LIGHT)
    assert Colors.BG_PRIMARY == Colors.LIGHT_BG_PRIMARY
    assert Colors.TEXT_PRIMARY == Colors.LIGHT_TEXT_PRIMARY
    assert Colors.PRIMARY == Colors.LIGHT_PRIMARY
    assert Colors.BORDER == Colors.LIGHT_BORDER


@pytest.mark.gui
def test_apply_theme_system_resolves(qapp):
    """SYSTEM should resolve to either DARK or LIGHT — Colors should match one of them."""
    apply_theme(qapp, ThemeType.SYSTEM)
    assert Colors.BG_PRIMARY in (Colors.DARK_BG_PRIMARY, Colors.LIGHT_BG_PRIMARY)


@pytest.mark.gui
def test_apply_theme_sets_stylesheet(qapp):
    """After apply_theme the app should have a non-empty stylesheet."""
    apply_theme(qapp, ThemeType.DARK)
    assert qapp.styleSheet()
