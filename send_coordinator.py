from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from recipient_manager import Recipient
from mail_sender import MailSender, SendResult
from template_engine import render


@dataclass
class MatchResult:
    recipient: Recipient
    pdf_path: Path | None


@dataclass
class SendReport:
    sent_at: datetime = field(default_factory=datetime.now)
    success: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.success)

    @property
    def failure_count(self) -> int:
        return len(self.failures)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    def to_text(self, year: str, month: str) -> str:
        lines = [
            f"送信日時: {self.sent_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"対象月: {year}年{month}月",
            "",
            f"成功 ({self.success_count}名):",
        ]
        for s in self.success:
            lines.append(f"  - {s}")
        lines += ["", f"失敗 ({self.failure_count}名):"]
        for f_ in self.failures:
            lines.append(f"  - {f_}")
        lines += ["", f"スキップ ({self.skip_count}名):"]
        for s in self.skipped:
            lines.append(f"  - {s}")
        return "\n".join(lines)


class SendCoordinator:
    def __init__(self, *, recipients: list[Recipient], pdf_paths: list[Path]):
        self._recipients = recipients
        self._pdf_paths = pdf_paths

    def match(self) -> list[MatchResult]:
        pdf_to_recipient: dict = {}
        for pdf_path in self._pdf_paths:
            best = None
            for r in self._recipients:
                if r.excluded:
                    continue
                if r.name and r.name in pdf_path.name:
                    if best is None or len(r.name) > len(best.name):
                        best = r
            if best is not None:
                pdf_to_recipient[pdf_path] = best
        return [
            MatchResult(
                recipient=r,
                pdf_path=next((p for p, recip in pdf_to_recipient.items() if recip == r), None),
            )
            for r in self._recipients
        ]

    def execute(
        self,
        *,
        match_results: list[MatchResult],
        gmail_address: str,
        gmail_app_password: str,
        subject: str,
        body_template: str,
        year: str,
        month: str,
    ) -> SendReport:
        sender = MailSender(gmail_address=gmail_address, gmail_app_password=gmail_app_password)
        report = SendReport()

        for mr in match_results:
            r = mr.recipient
            if r.excluded:
                report.skipped.append(f"{r.name} - 除外中")
                continue
            if mr.pdf_path is None:
                report.skipped.append(f"{r.name} - PDFなし")
                continue

            body = render(body_template, name=r.name, month=month, year=year)
            result = sender.send(
                to_email=r.email,
                subject=subject,
                body=body,
                pdf_path=mr.pdf_path,
            )
            if result == SendResult.SUCCESS:
                report.success.append(f"{r.name} <{r.email}>")
            else:
                report.failures.append(f"{r.name} <{r.email}> - {result.value}")

        return report
