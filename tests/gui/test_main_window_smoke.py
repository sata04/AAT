import pytest


@pytest.mark.gui
def test_main_window_initializes_with_controls_disabled(qtbot, monkeypatch, tmp_path):
    monkeypatch.setenv("AAT_CONFIG_DIR", str(tmp_path / "config_dir"))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from gui.main_window import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "AAT (Acceleration Analysis Tool)"
    assert window.g_quality_mode_button.isEnabled() is False
    assert window.show_all_button.isEnabled() is False
    assert window.compare_button.isEnabled() is False
