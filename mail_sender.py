import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path

class SendResult(Enum):
    SUCCESS = "success"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"

class MailSender:
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 465

    def __init__(self, gmail_address: str, gmail_app_password: str):
        self._address = gmail_address
        self._password = gmail_app_password

    def send(self, *, to_email: str, subject: str, body: str, pdf_path: Path) -> SendResult:
        msg = MIMEMultipart()
        msg["From"] = self._address
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with Path(pdf_path).open("rb") as f:
                part = MIMEApplication(f.read(), _subtype="pdf")
                part.add_header("Content-Disposition", "attachment", filename=Path(pdf_path).name)
                msg.attach(part)

            with smtplib.SMTP_SSL(self.SMTP_HOST, self.SMTP_PORT) as server:
                server.login(self._address, self._password)
                server.sendmail(self._address, to_email, msg.as_string())
            return SendResult.SUCCESS
        except smtplib.SMTPAuthenticationError:
            return SendResult.AUTH_ERROR
        except OSError:
            return SendResult.NETWORK_ERROR
