import json
import pytest
from pathlib import Path
from config import Config

@pytest.fixture
def tmp_config(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "gmail_address": "test@gmail.com",
        "gmail_app_password": "abcd efgh ijkl mnop",
        "subject_template": "{year}年{month}月分 給与明細",
        "body_template": "{name}様\n\n添付をご確認ください。",
        "filename_pattern_type": "contains"
    }), encoding="utf-8")
    return config_path

def test_load(tmp_config):
    cfg = Config(tmp_config)
    assert cfg.gmail_address == "test@gmail.com"
    assert cfg.gmail_app_password == "abcd efgh ijkl mnop"
    assert cfg.subject_template == "{year}年{month}月分 給与明細"
    assert cfg.filename_pattern_type == "contains"

def test_save(tmp_config):
    cfg = Config(tmp_config)
    cfg.gmail_address = "new@gmail.com"
    cfg.save()
    cfg2 = Config(tmp_config)
    assert cfg2.gmail_address == "new@gmail.com"

def test_is_configured_false(tmp_config):
    cfg = Config(tmp_config)
    cfg.gmail_address = ""
    assert cfg.is_configured() is False

def test_is_configured_true(tmp_config):
    cfg = Config(tmp_config)
    assert cfg.is_configured() is True

def test_missing_file_creates_defaults(tmp_path):
    config_path = tmp_path / "config.json"
    cfg = Config(config_path)
    assert cfg.gmail_address == ""
    assert cfg.subject_template == "{year}年{month}月分 給与明細"
