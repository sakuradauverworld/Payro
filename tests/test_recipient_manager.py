import pytest
from pathlib import Path
from recipient_manager import RecipientManager, Recipient, Group


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


def test_empty_data_dir_creates_no_groups(data_dir):
    mgr = RecipientManager(data_dir)
    assert mgr.groups == []


def test_add_group(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("テスト", "default")
    assert len(mgr.groups) == 1
    assert group.name == "テスト"
    assert group.template_id == "default"
    assert (data_dir / "groups.json").exists()


def test_remove_group(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("テスト", "default")
    mgr.add_recipient(group.id, Recipient(name="山田", email="yamada@example.com", filename_pattern="山田"))
    mgr.remove_group(group.id)
    assert mgr.groups == []
    assert not (data_dir / "groups" / f"{group.id}.csv").exists()


def test_duplicate_group(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("本社", "default")
    mgr.add_recipient(group.id, Recipient(name="山田", email="yamada@example.com", filename_pattern="山田"))
    new_group = mgr.duplicate_group(group.id)
    assert new_group.name == "本社 のコピー"
    assert new_group.template_id == "default"
    assert new_group.id != group.id
    assert len(mgr.get_recipients(new_group.id)) == 1
    assert mgr.get_recipients(new_group.id)[0].name == "山田"
    assert len(mgr.get_recipients(group.id)) == 1  # 元は変わらず


def test_update_group_name(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("旧名前", "default")
    mgr.update_group(group.id, name="新名前")
    assert mgr.groups[0].name == "新名前"


def test_update_group_template(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("テスト", "tmpl_a")
    mgr.update_group(group.id, template_id="tmpl_b")
    assert mgr.groups[0].template_id == "tmpl_b"


def test_add_and_get_recipient(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("テスト", "default")
    mgr.add_recipient(group.id, Recipient(name="山田", email="yamada@example.com", filename_pattern="山田"))
    recipients = mgr.get_recipients(group.id)
    assert len(recipients) == 1
    assert recipients[0].name == "山田"


def test_remove_recipient(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("テスト", "default")
    mgr.add_recipient(group.id, Recipient(name="山田", email="yamada@example.com", filename_pattern="山田"))
    mgr.add_recipient(group.id, Recipient(name="佐藤", email="sato@example.com", filename_pattern="佐藤"))
    mgr.remove_recipient(group.id, 0)
    recipients = mgr.get_recipients(group.id)
    assert len(recipients) == 1
    assert recipients[0].name == "佐藤"


def test_update_recipient(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("テスト", "default")
    mgr.add_recipient(group.id, Recipient(name="山田", email="yamada@example.com", filename_pattern="山田"))
    mgr.update_recipient(group.id, 0, Recipient(name="山田太郎", email="new@example.com", filename_pattern="山田"))
    assert mgr.get_recipients(group.id)[0].email == "new@example.com"


def test_save_and_reload(data_dir):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("テスト", "default")
    mgr.add_recipient(group.id, Recipient(name="山田", email="yamada@example.com", filename_pattern="山田"))
    mgr2 = RecipientManager(data_dir)
    assert len(mgr2.groups) == 1
    assert mgr2.groups[0].name == "テスト"
    assert len(mgr2.get_recipients(group.id)) == 1
    assert mgr2.get_recipients(group.id)[0].name == "山田"


def test_import_recipients(data_dir, tmp_path):
    mgr = RecipientManager(data_dir)
    group = mgr.add_group("テスト", "default")
    csv_path = tmp_path / "import.csv"
    csv_path.write_text("name,email,filename_pattern\n田中,tanaka@example.com,田中\n", encoding="utf-8")
    mgr.import_recipients(group.id, csv_path)
    recipients = mgr.get_recipients(group.id)
    assert len(recipients) == 1
    assert recipients[0].name == "田中"
    assert recipients[0].excluded is False


def test_csv_template_headers_no_excluded():
    headers = RecipientManager.csv_template_headers()
    assert "name" in headers
    assert "email" in headers
    assert "filename_pattern" in headers
    assert "excluded" not in headers


def test_recipient_excluded_default_false():
    r = Recipient(name="山田", email="yamada@example.com", filename_pattern="山田")
    assert r.excluded is False
