import json
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Template:
    id: str
    name: str
    subject: str
    body: str


class TemplateManager:
    def __init__(self, path: Path):
        self._path = Path(path)
        self.templates: list[Template] = []
        if self._path.exists():
            self._load()

    def _load(self):
        data = json.loads(self._path.read_text(encoding="utf-8"))
        self.templates = [Template(**t) for t in data]

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(
                [{"id": t.id, "name": t.name, "subject": t.subject, "body": t.body} for t in self.templates],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def add(self, name: str, subject: str, body: str) -> Template:
        tmpl = Template(id=str(uuid.uuid4()), name=name, subject=subject, body=body)
        self.templates.append(tmpl)
        self.save()
        return tmpl

    def remove(self, template_id: str):
        self.templates = [t for t in self.templates if t.id != template_id]
        self.save()

    def update(self, template_id: str, *, name: str | None = None, subject: str | None = None, body: str | None = None):
        tmpl = next(t for t in self.templates if t.id == template_id)
        if name is not None:
            tmpl.name = name
        if subject is not None:
            tmpl.subject = subject
        if body is not None:
            tmpl.body = body
        self.save()

    def get_by_id(self, template_id: str) -> Template | None:
        return next((t for t in self.templates if t.id == template_id), None)
