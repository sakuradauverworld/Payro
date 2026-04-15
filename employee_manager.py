import csv
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Employee:
    name: str
    email: str
    filename_pattern: str

class EmployeeManager:
    def __init__(self, path: Path):
        self._path = Path(path)
        self.employees: list[Employee] = []
        if self._path.exists():
            self._load()

    def _load(self):
        with self._path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            self.employees = [
                Employee(
                    name=row["name"],
                    email=row["email"],
                    filename_pattern=row["filename_pattern"],
                )
                for row in reader
            ]

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "email", "filename_pattern"])
            writer.writeheader()
            for emp in self.employees:
                writer.writerow({"name": emp.name, "email": emp.email, "filename_pattern": emp.filename_pattern})

    def add(self, employee: Employee):
        self.employees.append(employee)

    def remove(self, index: int):
        self.employees.pop(index)

    def update(self, index: int, employee: Employee):
        self.employees[index] = employee

    def find_by_filename(self, filename: str) -> Employee | None:
        sorted_employees = sorted(self.employees, key=lambda e: len(e.filename_pattern), reverse=True)
        for emp in sorted_employees:
            if emp.filename_pattern and emp.filename_pattern in filename:
                return emp
        return None
