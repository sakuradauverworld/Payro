import json
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def tmp_config(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "gmail_address": "test@gmail.com",
        "filename_pattern_type": "contains"
    }), encoding="utf-8")
    return config_path


def test_load(tmp_config):
    with patch("keyring.get_password", return_value="abcd efgh ijkl mnop"), \
         patch("keyring.set_password"):
        from config import Config
        cfg = Config(tmp_config)
        assert cfg.gmail_address == "test@gmail.com"
        assert cfg.gmail_app_password == "abcd efgh ijkl mnop"
        assert cfg.filename_pattern_type == "contains"


def test_save(tmp_config):
    with patch("keyring.get_password", return_value="abcd efgh ijkl mnop"), \
         patch("keyring.set_password") as mock_set:
        from config import Config
        cfg = Config(tmp_config)
        cfg.gmail_address = "new@gmail.com"
        cfg.save()
        mock_set.assert_called_with("payro", "gmail_app_password", "abcd efgh ijkl mnop")

    with patch("keyring.get_password", return_value="abcd efgh ijkl mnop"), \
         patch("keyring.set_password"):
        from config import Config
        cfg2 = Config(tmp_config)
        assert cfg2.gmail_address == "new@gmail.com"


def test_save_does_not_write_password_to_json(tmp_config):
    with patch("keyring.get_password", return_value="secret"), \
         patch("keyring.set_password"):
        from config import Config
        cfg = Config(tmp_config)
        cfg.gmail_app_password = "secret"
        cfg.save()

    saved = json.loads(tmp_config.read_text(encoding="utf-8"))
    assert "gmail_app_password" not in saved


def test_is_configured_false(tmp_config):
    with patch("keyring.get_password", return_value=""), \
         patch("keyring.set_password"):
        from config import Config
        cfg = Config(tmp_config)
        cfg.gmail_address = ""
        assert cfg.is_configured() is False


def test_is_configured_true(tmp_config):
    with patch("keyring.get_password", return_value="abcd efgh ijkl mnop"), \
         patch("keyring.set_password"):
        from config import Config
        cfg = Config(tmp_config)
        assert cfg.is_configured() is True


def test_missing_file_creates_defaults(tmp_path):
    config_path = tmp_path / "config.json"
    with patch("keyring.get_password", return_value=""), \
         patch("keyring.set_password"):
        from config import Config
        cfg = Config(config_path)
        assert cfg.gmail_address == ""
        assert cfg.gmail_app_password == ""


def test_migration_from_old_json(tmp_path):
    """旧バージョンの config.json（パスワード平文）から keyring へ移行する"""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "gmail_address": "user@gmail.com",
        "gmail_app_password": "old_plain_password",
        "filename_pattern_type": "contains"
    }), encoding="utf-8")

    with patch("keyring.set_password") as mock_set, \
         patch("keyring.get_password", return_value="old_plain_password"):
        from config import Config
        cfg = Config(config_path)
        mock_set.assert_any_call("payro", "gmail_app_password", "old_plain_password")
        saved = json.loads(config_path.read_text(encoding="utf-8"))
        assert "gmail_app_password" not in saved
        assert cfg.gmail_app_password == "old_plain_password"
