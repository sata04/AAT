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


@pytest.mark.gui
def test_g_quality_finish_error_does_not_persist_empty_results(qtbot, monkeypatch, tmp_path):
    monkeypatch.setenv("AAT_CONFIG_DIR", str(tmp_path / "config_dir"))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from gui.main_window import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)
    window.processed_data["dataset"] = {}

    shown_errors = []
    monkeypatch.setattr(window, "_show_error_dialog", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    window.on_g_quality_analysis_finished([], "dataset", None, error_message="boom")

    assert "g_quality_data" not in window.processed_data["dataset"]
    assert shown_errors
