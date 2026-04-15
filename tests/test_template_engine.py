from template_engine import render

def test_render_name_and_month():
    result = render("{name}様、{month}月分の給与明細を送付します。", name="山田太郎", month="4", year="2026")
    assert result == "山田太郎様、4月分の給与明細を送付します。"

def test_render_year():
    result = render("{year}年{month}月分 給与明細", name="佐藤花子", month="12", year="2026")
    assert result == "2026年12月分 給与明細"

def test_render_unknown_placeholder_remains():
    result = render("{name}様、{unknown}はそのまま", name="山田太郎", month="4", year="2026")
    assert result == "山田太郎様、{unknown}はそのまま"
