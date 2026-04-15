import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from employee_manager import Employee
from mail_sender import SendResult
from send_coordinator import SendCoordinator, MatchResult, SendReport

@pytest.fixture
def employees():
    return [
        Employee(name="山田太郎", email="yamada@example.com", filename_pattern="山田太郎"),
        Employee(name="佐藤花子", email="sato@example.com", filename_pattern="佐藤花子"),
        Employee(name="田中次郎", email="tanaka@example.com", filename_pattern="田中次郎"),
    ]

@pytest.fixture
def pdf_paths(tmp_path):
    p1 = tmp_path / "給与明細_山田太郎_202604.pdf"
    p2 = tmp_path / "給与明細_佐藤花子_202604.pdf"
    p1.write_bytes(b"%PDF fake")
    p2.write_bytes(b"%PDF fake")
    return [p1, p2]

def test_match(employees, pdf_paths):
    coord = SendCoordinator(employees=employees, pdf_paths=pdf_paths)
    results = coord.match()
    matched = [r for r in results if r.pdf_path is not None]
    unmatched = [r for r in results if r.pdf_path is None]
    assert len(matched) == 2
    assert len(unmatched) == 1
    assert unmatched[0].employee.name == "田中次郎"

@patch("send_coordinator.MailSender")
def test_execute_skips_unmatched(mock_sender_class, employees, pdf_paths):
    mock_sender = MagicMock()
    mock_sender.send.return_value = SendResult.SUCCESS
    mock_sender_class.return_value = mock_sender

    coord = SendCoordinator(employees=employees, pdf_paths=pdf_paths)
    match_results = coord.match()
    report = coord.execute(
        match_results=match_results,
        gmail_address="test@gmail.com",
        gmail_app_password="xxxx",
        subject="給与明細",
        body_template="{name}様",
        year="2026",
        month="4",
    )
    assert report.success_count == 2
    assert report.skip_count == 1
    assert report.failure_count == 0

@patch("send_coordinator.MailSender")
def test_execute_records_failure(mock_sender_class, employees, pdf_paths):
    mock_sender = MagicMock()
    mock_sender.send.return_value = SendResult.NETWORK_ERROR
    mock_sender_class.return_value = mock_sender

    coord = SendCoordinator(employees=employees, pdf_paths=pdf_paths)
    match_results = coord.match()
    report = coord.execute(
        match_results=match_results,
        gmail_address="test@gmail.com",
        gmail_app_password="xxxx",
        subject="給与明細",
        body_template="{name}様",
        year="2026",
        month="4",
    )
    assert report.failure_count == 2
    assert report.success_count == 0
