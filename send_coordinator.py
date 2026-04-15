from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from employee_manager import Employee
from mail_sender import MailSender, SendResult
from template_engine import render


@dataclass
class MatchResult:
    employee: Employee
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
    def __init__(self, *, employees: list[Employee], pdf_paths: list[Path]):
        self._employees = employees
        self._pdf_paths = pdf_paths

    def match(self) -> list[MatchResult]:
        pdf_to_employee: dict = {}
        for pdf_path in self._pdf_paths:
            best = None
            for emp in self._employees:
                if emp.excluded:
                    continue
                if emp.filename_pattern and emp.filename_pattern in pdf_path.name:
                    if best is None or len(emp.filename_pattern) > len(best.filename_pattern):
                        best = emp
            if best is not None:
                pdf_to_employee[pdf_path] = best
        return [
            MatchResult(
                employee=emp,
                pdf_path=next((p for p, e in pdf_to_employee.items() if e == emp), None),
            )
            for emp in self._employees
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
            emp = mr.employee
            if emp.excluded:
                report.skipped.append(f"{emp.name} - 除外中")
                continue
            if mr.pdf_path is None:
                report.skipped.append(f"{emp.name} - PDFなし")
                continue

            body = render(body_template, name=emp.name, month=month, year=year)
            result = sender.send(
                to_email=emp.email,
                subject=subject,
                body=body,
                pdf_path=mr.pdf_path,
            )
            if result == SendResult.SUCCESS:
                report.success.append(f"{emp.name} <{emp.email}>")
            else:
                report.failures.append(f"{emp.name} <{emp.email}> - {result.value}")

        return report
