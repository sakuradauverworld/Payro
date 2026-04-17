import json
import pytest
from pathlib import Path
from migration import migrate


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    return d


def test_migrate_from_scratch(data_dir):
    config_path = data_dir / "config.json"
    migrate(data_dir, config_path)
    assert (data_dir / "groups.json").exists()
    assert (data_dir / "templates.json").exists()
    groups = json.loads((data_dir / "groups.json").read_text(encoding="utf-8"))
    assert len(groups) == 1
    assert groups[0]["id"] == "default"
    templates = json.loads((data_dir / "templates.json").read_text(encoding="utf-8"))
    assert len(templates) == 1
    assert templates[0]["id"] == "default"


def test_migrate_copies_employees_csv(data_dir):
    config_path = data_dir / "config.json"
    (data_dir / "employees.csv").write_text(
        "name,email,filename_pattern\n山田太郎,yamada@example.com,山田太郎\n",
        encoding="utf-8",
    )
    migrate(data_dir, config_path)
    assert (data_dir / "groups" / "default.csv").exists()
    content = (data_dir / "groups" / "default.csv").read_text(encoding="utf-8")
    assert "山田太郎" in content


def test_migrate_preserves_template_from_config(data_dir):
    config_path = data_dir / "config.json"
    config_path.write_text(
        json.dumps({
            "gmail_address": "test@gmail.com",
            "subject_template": "カスタム件名",
            "body_template": "カスタム本文",
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    migrate(data_dir, config_path)
    templates = json.loads((data_dir / "templates.json").read_text(encoding="utf-8"))
    assert templates[0]["subject"] == "カスタム件名"
    assert templates[0]["body"] == "カスタム本文"


def test_migrate_removes_template_from_config(data_dir):
    config_path = data_dir / "config.json"
    config_path.write_text(
        json.dumps({
            "gmail_address": "test@gmail.com",
            "subject_template": "カスタム件名",
            "body_template": "カスタム本文",
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    migrate(data_dir, config_path)
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    assert "subject_template" not in cfg
    assert "body_template" not in cfg
    assert cfg["gmail_address"] == "test@gmail.com"


def test_migrate_is_idempotent(data_dir):
    config_path = data_dir / "config.json"
    migrate(data_dir, config_path)
    migrate(data_dir, config_path)  # 2 回目は何もしない
    groups = json.loads((data_dir / "groups.json").read_text(encoding="utf-8"))
    assert len(groups) == 1  # 重複しない


def test_migrate_no_employees_csv(data_dir):
    config_path = data_dir / "config.json"
    migrate(data_dir, config_path)
    assert not (data_dir / "groups" / "default.csv").exists()
