import json

from core.config import load_config, save_config
from core.version import APP_VERSION


def test_load_config_creates_user_file_when_missing(app_root_with_default, tmp_path, monkeypatch, dummy_message_box):
    default_config, _ = app_root_with_default
    user_dir = tmp_path / "user_dir"
    monkeypatch.setenv("AAT_CONFIG_DIR", str(user_dir))

    config = load_config()

    assert (user_dir / "config.json").exists()
    assert config["time_column"] == default_config["time_column"]
    assert config["app_version"] == APP_VERSION


def test_load_config_handles_invalid_user_json(app_root_with_default, tmp_path, monkeypatch, dummy_message_box):
    default_config, _ = app_root_with_default
    user_dir = tmp_path / "user_dir"
    user_dir.mkdir(parents=True)
    monkeypatch.setenv("AAT_CONFIG_DIR", str(user_dir))
    (user_dir / "config.json").write_text("{invalid json", encoding="utf-8")

    config = load_config()

    assert config["time_column"] == default_config["time_column"]
    assert config["app_version"] == APP_VERSION


def test_load_config_migrates_legacy_config(app_root_with_default, tmp_path, monkeypatch, dummy_message_box):
    _, app_root = app_root_with_default
    user_dir = tmp_path / "user_dir"
    monkeypatch.setenv("AAT_CONFIG_DIR", str(user_dir))

    legacy_config_path = app_root / "config.json"
    legacy_backup_path = app_root / "config.json.bak"
    legacy_config_path.write_text(json.dumps({"time_column": "legacy_time"}), encoding="utf-8")
    legacy_backup_path.write_text("backup", encoding="utf-8")

    config = load_config()

    assert config["time_column"] == "legacy_time"
    assert (user_dir / "config.json").exists()
    assert not legacy_config_path.exists()
    assert (user_dir / "config.json.bak").exists()


def test_save_config_creates_backup_for_existing_file(tmp_path, monkeypatch, dummy_message_box):
    user_dir = tmp_path / "user_dir"
    monkeypatch.setenv("AAT_CONFIG_DIR", str(user_dir))
    user_dir.mkdir(parents=True)

    config_path = user_dir / "config.json"
    config_path.write_text(json.dumps({"old": 1}), encoding="utf-8")

    result = save_config({"new": 2})

    assert result is True
    assert json.loads(config_path.read_text(encoding="utf-8"))["new"] == 2
    backup_path = user_dir / "config.json.bak"
    assert backup_path.exists()
    assert json.loads(backup_path.read_text(encoding="utf-8"))["old"] == 1
