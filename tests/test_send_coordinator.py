import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from recipient_manager import Recipient
from mail_sender import SendResult
from send_coordinator import SendCoordinator, MatchResult, SendReport


@pytest.fixture
def recipients():
    return [
        Recipient(name="山田太郎", email="yamada@example.com"),
        Recipient(name="佐藤花子", email="sato@example.com"),
        Recipient(name="田中次郎", email="tanaka@example.com"),
    ]

@pytest.fixture
def pdf_paths(tmp_path):
    p1 = tmp_path / "給与明細_山田太郎_202604.pdf"
    p2 = tmp_path / "給与明細_佐藤花子_202604.pdf"
    p1.write_bytes(b"%PDF fake")
    p2.write_bytes(b"%PDF fake")
    return [p1, p2]

def test_match(recipients, pdf_paths):
    coord = SendCoordinator(recipients=recipients, pdf_paths=pdf_paths)
    results = coord.match()
    matched = [r for r in results if r.pdf_path is not None]
    unmatched = [r for r in results if r.pdf_path is None]
    assert len(matched) == 2
    assert len(unmatched) == 1
    assert unmatched[0].recipient.name == "田中次郎"

@patch("send_coordinator.MailSender")
def test_execute_skips_unmatched(mock_sender_class, recipients, pdf_paths):
    mock_sender = MagicMock()
    mock_sender.send.return_value = SendResult.SUCCESS
    mock_sender_class.return_value = mock_sender

    coord = SendCoordinator(recipients=recipients, pdf_paths=pdf_paths)
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
    assert "田中次郎 - PDFなし" in report.skipped

def test_match_longest_name_wins(tmp_path):
    """「田中」が「田中太郎.pdf」を奪わないことを確認"""
    recipients = [
        Recipient(name="田中", email="tanaka@example.com"),
        Recipient(name="田中太郎", email="tanaka.taro@example.com"),
    ]
    pdf = tmp_path / "給与明細_田中太郎_202604.pdf"
    pdf.write_bytes(b"%PDF fake")
    coord = SendCoordinator(recipients=recipients, pdf_paths=[pdf])
    results = coord.match()
    taro = next(r for r in results if r.recipient.name == "田中太郎")
    tanaka = next(r for r in results if r.recipient.name == "田中")
    assert taro.pdf_path == pdf
    assert tanaka.pdf_path is None


@patch("send_coordinator.MailSender")
def test_execute_records_failure(mock_sender_class, recipients, pdf_paths):
    mock_sender = MagicMock()
    mock_sender.send.return_value = SendResult.NETWORK_ERROR
    mock_sender_class.return_value = mock_sender

    coord = SendCoordinator(recipients=recipients, pdf_paths=pdf_paths)
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


def test_match_excluded_recipient_has_no_pdf(tmp_path):
    """除外中の宛先は PDF があってもマッチしないこと"""
    recipients = [
        Recipient(name="山田太郎", email="yamada@example.com", excluded=True),
    ]
    pdf = tmp_path / "給与明細_山田太郎_202604.pdf"
    pdf.write_bytes(b"%PDF fake")
    coord = SendCoordinator(recipients=recipients, pdf_paths=[pdf])
    results = coord.match()
    assert results[0].pdf_path is None


def test_match_excluded_does_not_steal_pdf(tmp_path):
    """除外中の宛先が他の宛先の PDF を奪わないこと"""
    recipients = [
        Recipient(name="山田太郎", email="yamada@example.com", excluded=True),
        Recipient(name="佐藤花子", email="sato@example.com"),
    ]
    pdf_yamada = tmp_path / "給与明細_山田太郎_202604.pdf"
    pdf_sato = tmp_path / "給与明細_佐藤花子_202604.pdf"
    pdf_yamada.write_bytes(b"%PDF fake")
    pdf_sato.write_bytes(b"%PDF fake")
    coord = SendCoordinator(recipients=recipients, pdf_paths=[pdf_yamada, pdf_sato])
    results = coord.match()
    yamada_result = next(r for r in results if r.recipient.name == "山田太郎")
    sato_result = next(r for r in results if r.recipient.name == "佐藤花子")
    assert yamada_result.pdf_path is None
    assert sato_result.pdf_path == pdf_sato


@patch("send_coordinator.MailSender")
def test_execute_skips_excluded(mock_sender_class, tmp_path):
    """execute() が除外中の宛先をスキップしてレポートに記録すること"""
    mock_sender = MagicMock()
    mock_sender.send.return_value = SendResult.SUCCESS
    mock_sender_class.return_value = mock_sender

    recipients = [
        Recipient(name="山田太郎", email="yamada@example.com", excluded=True),
        Recipient(name="佐藤花子", email="sato@example.com"),
    ]
    pdf = tmp_path / "給与明細_佐藤花子_202604.pdf"
    pdf.write_bytes(b"%PDF fake")
    coord = SendCoordinator(recipients=recipients, pdf_paths=[pdf])
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
    assert report.success_count == 1
    assert report.skip_count == 1
    assert "山田太郎 - 除外中" in report.skipped
