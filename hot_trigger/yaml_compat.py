from __future__ import annotations

import json
from typing import Any

try:
    import yaml as _yaml
except ModuleNotFoundError:  # pragma: no cover
    _yaml = None


def _parse_scalar(value: str):
    v = value.strip()
    if not v:
        return ""
    if v.lower() in {"true", "false"}:
        return v.lower() == "true"
    if v.lower() in {"null", "none"}:
        return None
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        return json.loads(v.replace("'", '"'))
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def _simple_yaml_load(text: str) -> Any:
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for line in lines:
        indent = len(line) - len(line.lstrip(" "))
        key, _, raw_val = line.strip().partition(":")
        val = raw_val.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        current = stack[-1][1]

        if val == "":
            current[key] = {}
            stack.append((indent, current[key]))
        else:
            current[key] = _parse_scalar(val)
    return root


def safe_load(text: str) -> Any:
    if _yaml:
        return _yaml.safe_load(text)
    return _simple_yaml_load(text)


def safe_dump(data: Any, *, allow_unicode: bool = True, sort_keys: bool = False) -> str:
    if _yaml:
        return _yaml.safe_dump(data, allow_unicode=allow_unicode, sort_keys=sort_keys)
    return json.dumps(data, ensure_ascii=not allow_unicode, indent=2)
