import smtplib
from unittest.mock import MagicMock, patch
from pathlib import Path
from mail_sender import MailSender, SendResult

@patch("mail_sender.smtplib.SMTP_SSL")
def test_send_success(mock_smtp_class, tmp_path):
    pdf = tmp_path / "山田太郎_202604.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    mock_server = MagicMock()
    mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

    sender = MailSender(gmail_address="test@gmail.com", gmail_app_password="xxxx")
    result = sender.send(
        to_email="yamada@example.com",
        subject="2026年4月分 給与明細",
        body="山田太郎様\n\n添付をご確認ください。",
        pdf_path=pdf,
    )
    assert result == SendResult.SUCCESS
    assert mock_server.sendmail.called

@patch("mail_sender.smtplib.SMTP_SSL")
def test_send_auth_failure(mock_smtp_class, tmp_path):
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    mock_smtp_class.return_value.__enter__.side_effect = smtplib.SMTPAuthenticationError(535, b"Bad credentials")

    sender = MailSender(gmail_address="bad@gmail.com", gmail_app_password="wrong")
    result = sender.send(
        to_email="yamada@example.com",
        subject="件名",
        body="本文",
        pdf_path=pdf,
    )
    assert result == SendResult.AUTH_ERROR

@patch("mail_sender.smtplib.SMTP_SSL")
def test_send_network_failure(mock_smtp_class, tmp_path):
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    mock_smtp_class.return_value.__enter__.side_effect = OSError("Connection refused")

    sender = MailSender(gmail_address="test@gmail.com", gmail_app_password="xxxx")
    result = sender.send(
        to_email="yamada@example.com",
        subject="件名",
        body="本文",
        pdf_path=pdf,
    )
    assert result == SendResult.NETWORK_ERROR
