import json
import shutil
from pathlib import Path


def migrate(data_dir: Path, config_path: Path) -> None:
    """旧データを新構造に移行する（べき等: groups.json が存在すればスキップ）"""
    groups_json = data_dir / "groups.json"
    if groups_json.exists():
        return

    data_dir.mkdir(parents=True, exist_ok=True)

    # config.json から旧テンプレートを読み出して削除する
    subject = "{year}年{month}月 給与明細"
    body = "{name}様\n\nお疲れ様です。\n{year}年{month}月分の給与明細を送付いたします。"

    if config_path.exists():
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        subject = cfg.pop("subject_template", subject)
        body = cfg.pop("body_template", body)
        config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    # templates.json を作成
    templates_json = data_dir / "templates.json"
    templates_json.write_text(
        json.dumps(
            [{"id": "default", "name": "給料明細", "subject": subject, "body": body}],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # groups.json を作成
    groups_json.write_text(
        json.dumps(
            [{"id": "default", "name": "La pilates ○○店", "template_id": "default"}],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # employees.csv → groups/default.csv にコピー
    old_csv = data_dir / "employees.csv"
    if old_csv.exists():
        groups_dir = data_dir / "groups"
        groups_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(old_csv, groups_dir / "default.csv")
