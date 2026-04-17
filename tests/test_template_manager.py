import pytest
from pathlib import Path
from template_manager import TemplateManager, Template


@pytest.fixture
def tmpl_path(tmp_path):
    return tmp_path / "templates.json"


def test_empty_file_creates_no_templates(tmpl_path):
    mgr = TemplateManager(tmpl_path)
    assert mgr.templates == []


def test_add_template(tmpl_path):
    mgr = TemplateManager(tmpl_path)
    tmpl = mgr.add("テスト", "件名", "本文")
    assert len(mgr.templates) == 1
    assert tmpl.name == "テスト"
    assert tmpl.subject == "件名"
    assert tmpl.body == "本文"


def test_remove_template(tmpl_path):
    mgr = TemplateManager(tmpl_path)
    tmpl = mgr.add("テスト", "件名", "本文")
    mgr.remove(tmpl.id)
    assert mgr.templates == []


def test_update_template(tmpl_path):
    mgr = TemplateManager(tmpl_path)
    tmpl = mgr.add("テスト", "旧件名", "旧本文")
    mgr.update(tmpl.id, name="新テスト", subject="新件名")
    assert mgr.templates[0].name == "新テスト"
    assert mgr.templates[0].subject == "新件名"
    assert mgr.templates[0].body == "旧本文"  # 変更なし


def test_get_by_id(tmpl_path):
    mgr = TemplateManager(tmpl_path)
    tmpl = mgr.add("テスト", "件名", "本文")
    found = mgr.get_by_id(tmpl.id)
    assert found is not None
    assert found.name == "テスト"


def test_get_by_id_not_found(tmpl_path):
    mgr = TemplateManager(tmpl_path)
    assert mgr.get_by_id("nonexistent") is None


def test_save_and_reload(tmpl_path):
    mgr = TemplateManager(tmpl_path)
    tmpl = mgr.add("テスト", "件名", "本文")
    mgr2 = TemplateManager(tmpl_path)
    assert len(mgr2.templates) == 1
    assert mgr2.templates[0].name == "テスト"
    assert mgr2.get_by_id(tmpl.id) is not None
