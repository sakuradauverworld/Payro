import pytest
from pathlib import Path
from employee_manager import EmployeeManager, Employee

@pytest.fixture
def tmp_csv(tmp_path):
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "name,email,filename_pattern\n山田太郎,yamada@example.com,山田太郎\n佐藤花子,sato@example.com,佐藤花子\n",
        encoding="utf-8"
    )
    return csv_path

def test_load(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    assert len(mgr.employees) == 2
    assert mgr.employees[0].name == "山田太郎"
    assert mgr.employees[0].email == "yamada@example.com"
    assert mgr.employees[0].filename_pattern == "山田太郎"

def test_add_and_save(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    mgr.add(Employee(name="田中次郎", email="tanaka@example.com", filename_pattern="田中次郎"))
    mgr.save()
    mgr2 = EmployeeManager(tmp_csv)
    assert len(mgr2.employees) == 3
    assert mgr2.employees[2].name == "田中次郎"

def test_remove(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    mgr.remove(0)
    assert len(mgr.employees) == 1
    assert mgr.employees[0].name == "佐藤花子"

def test_update(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    mgr.update(0, Employee(name="山田太郎", email="new@example.com", filename_pattern="山田太郎"))
    assert mgr.employees[0].email == "new@example.com"

def test_find_by_filename(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    emp = mgr.find_by_filename("給与明細_山田太郎_202604.pdf")
    assert emp is not None
    assert emp.name == "山田太郎"

def test_find_by_filename_no_match(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    emp = mgr.find_by_filename("給与明細_鈴木一郎_202604.pdf")
    assert emp is None

def test_missing_file_creates_empty(tmp_path):
    mgr = EmployeeManager(tmp_path / "employees.csv")
    assert mgr.employees == []

def test_find_by_filename_longest_pattern_wins(tmp_path):
    """短いパターンと長いパターンが両方マッチする場合、長い方が優先される"""
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "name,email,filename_pattern\n田中,tanaka@example.com,田中\n田中太郎,taro@example.com,田中太郎\n",
        encoding="utf-8"
    )
    mgr = EmployeeManager(csv_path)
    emp = mgr.find_by_filename("給与明細_田中太郎_202604.pdf")
    assert emp is not None
    assert emp.name == "田中太郎"

def test_find_by_filename_shorter_pattern_still_works(tmp_path):
    """長いパターンがマッチしない場合、短いパターンにフォールバックする"""
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "name,email,filename_pattern\n田中,tanaka@example.com,田中\n田中太郎,taro@example.com,田中太郎\n",
        encoding="utf-8"
    )
    mgr = EmployeeManager(csv_path)
    emp = mgr.find_by_filename("給与明細_田中_202604.pdf")
    assert emp is not None
    assert emp.name == "田中"

def test_excluded_default_false():
    emp = Employee(name="山田太郎", email="yamada@example.com", filename_pattern="山田太郎")
    assert emp.excluded is False

def test_load_no_excluded_column(tmp_path):
    """excluded 列のない旧 CSV を読み込んでも excluded=False になること"""
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "name,email,filename_pattern\n山田太郎,yamada@example.com,山田太郎\n",
        encoding="utf-8"
    )
    mgr = EmployeeManager(csv_path)
    assert mgr.employees[0].excluded is False

def test_load_excluded_column(tmp_path):
    """excluded 列がある CSV を読み込んで excluded=True になること"""
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "name,email,filename_pattern,excluded\n山田太郎,yamada@example.com,山田太郎,True\n",
        encoding="utf-8"
    )
    mgr = EmployeeManager(csv_path)
    assert mgr.employees[0].excluded is True

def test_save_includes_excluded(tmp_path):
    """save() が excluded 列を CSV に書き出すこと"""
    csv_path = tmp_path / "employees.csv"
    mgr = EmployeeManager(csv_path)
    mgr.add(Employee(name="山田太郎", email="yamada@example.com", filename_pattern="山田太郎", excluded=True))
    mgr.save()
    mgr2 = EmployeeManager(csv_path)
    assert mgr2.employees[0].excluded is True
