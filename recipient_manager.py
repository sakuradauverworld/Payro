import csv
import json
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Recipient:
    name: str
    email: str
    excluded: bool = False


@dataclass
class Group:
    id: str
    name: str
    template_id: str


class RecipientManager:
    def __init__(self, data_dir: Path):
        self._data_dir = Path(data_dir)
        self._groups_json = self._data_dir / "groups.json"
        self._groups_dir = self._data_dir / "groups"
        self.groups: list[Group] = []
        self._recipients: dict[str, list[Recipient]] = {}
        if self._groups_json.exists():
            self._load()

    def _load(self):
        data = json.loads(self._groups_json.read_text(encoding="utf-8"))
        self.groups = [Group(**g) for g in data]
        for group in self.groups:
            csv_path = self._groups_dir / f"{group.id}.csv"
            self._recipients[group.id] = self._load_csv(csv_path)

    @staticmethod
    def _load_csv(path: Path) -> list[Recipient]:
        if not path.exists():
            return []
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return [
                Recipient(
                    name=row["name"],
                    email=row["email"],
                    excluded=row.get("excluded", "False") == "True",
                )
                for row in reader
            ]

    def save_groups(self):
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._groups_json.write_text(
            json.dumps(
                [{"id": g.id, "name": g.name, "template_id": g.template_id} for g in self.groups],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def save_recipients(self, group_id: str):
        self._groups_dir.mkdir(parents=True, exist_ok=True)
        path = self._groups_dir / f"{group_id}.csv"
        recipients = self._recipients.get(group_id, [])
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "email", "excluded"])
            writer.writeheader()
            for r in recipients:
                writer.writerow({
                    "name": r.name,
                    "email": r.email,
                    "excluded": r.excluded,
                })

    def get_recipients(self, group_id: str) -> list[Recipient]:
        return self._recipients.get(group_id, [])

    def add_group(self, name: str, template_id: str) -> Group:
        group = Group(id=str(uuid.uuid4()), name=name, template_id=template_id)
        self.groups.append(group)
        self._recipients[group.id] = []
        self.save_groups()
        return group

    def remove_group(self, group_id: str):
        self.groups = [g for g in self.groups if g.id != group_id]
        self._recipients.pop(group_id, None)
        csv_path = self._groups_dir / f"{group_id}.csv"
        if csv_path.exists():
            csv_path.unlink()
        self.save_groups()

    def duplicate_group(self, group_id: str) -> Group:
        original = next(g for g in self.groups if g.id == group_id)
        new_group = Group(
            id=str(uuid.uuid4()),
            name=f"{original.name} のコピー",
            template_id=original.template_id,
        )
        self.groups.append(new_group)
        self._recipients[new_group.id] = [
            Recipient(name=r.name, email=r.email, excluded=r.excluded)
            for r in self._recipients.get(group_id, [])
        ]
        self.save_groups()
        self.save_recipients(new_group.id)
        return new_group

    def update_group(self, group_id: str, *, name: str | None = None, template_id: str | None = None):
        group = next(g for g in self.groups if g.id == group_id)
        if name is not None:
            group.name = name
        if template_id is not None:
            group.template_id = template_id
        self.save_groups()

    def add_recipient(self, group_id: str, recipient: Recipient):
        self._recipients.setdefault(group_id, []).append(recipient)
        self.save_recipients(group_id)

    def remove_recipient(self, group_id: str, index: int):
        self._recipients[group_id].pop(index)
        self.save_recipients(group_id)

    def update_recipient(self, group_id: str, index: int, recipient: Recipient):
        self._recipients[group_id][index] = recipient
        self.save_recipients(group_id)

    def import_recipients(self, group_id: str, csv_path: Path):
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            new_recipients = [
                Recipient(
                    name=row["name"],
                    email=row["email"],
                    excluded=False,
                )
                for row in reader
            ]
        self._recipients.setdefault(group_id, []).extend(new_recipients)
        self.save_recipients(group_id)

    @staticmethod
    def csv_template_headers() -> str:
        return "name,email\n"
