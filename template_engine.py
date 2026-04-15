def render(template: str, *, name: str, month: str, year: str) -> str:
    return template.format_map(_SafeDict(name=name, month=month, year=year))

class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
