"""File writer + YAML subset used by emit.py (stdlib only)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def write(out: Path, rel: str, content: str) -> Path:
    dest = out / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    dest.write_text(content, encoding="utf-8")
    return dest


def dump_json(obj: Any) -> str:
    return json.dumps(obj, indent=2) + "\n"


def _needs_quotes(value: str) -> bool:
    if value == "":
        return True
    if re.match(r"^[:\-?&*!|>'\"%@`{}[\],]|^\s|\s$", value):
        return True
    if re.match(r"^(true|false|null|yes|no|on|off)$", value, re.I):
        return True
    if re.match(r"^-?\d+(\.\d+)?$", value):
        return True
    if ":" in value or "#" in value or "\n" in value:
        return True
    return False


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_yaml(value: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    if isinstance(value, str):
        if "\n" in value:
            lines = value.rstrip("\n").split("\n")
            return "|\n" + "\n".join(f"{'  ' * (indent + 1)}{line}" for line in lines)
        return _quote(value) if _needs_quotes(value) else value
    if isinstance(value, list):
        if not value:
            return "[]"
        rows: list[str] = []
        for item in value:
            if isinstance(item, dict):
                entries = [(k, v) for k, v in item.items() if v is not None]
                if not entries:
                    rows.append(f"{pad}- {{}}")
                    continue
                first_k, first_v = entries[0]
                first = f"{first_k}: {to_yaml(first_v, indent + 1)}"
                rest = []
                for k, v in entries[1:]:
                    dumped = to_yaml(v, indent + 1)
                    if isinstance(v, dict) and v:
                        rest.append(f"{pad}  {k}:\n{dumped}")
                    elif isinstance(v, list) and v:
                        rest.append(f"{pad}  {k}:\n{dumped}")
                    else:
                        rest.append(f"{pad}  {k}: {dumped}")
                block = f"{pad}- {first}"
                if rest:
                    block += "\n" + "\n".join(rest)
                rows.append(block)
            else:
                rows.append(f"{pad}- {to_yaml(item, indent + 1)}")
        return "\n".join(rows)
    if isinstance(value, dict):
        entries = [(k, v) for k, v in value.items() if v is not None]
        if not entries:
            return "{}"
        rows = []
        for k, v in entries:
            if isinstance(v, dict):
                inner = to_yaml(v, indent + 1)
                rows.append(f"{pad}{k}: {{}}" if inner == "{}" else f"{pad}{k}:\n{inner}")
            elif isinstance(v, list):
                if not v:
                    rows.append(f"{pad}{k}: []")
                else:
                    rows.append(f"{pad}{k}:\n{to_yaml(v, indent + 1)}")
            else:
                dumped = to_yaml(v, indent)
                if isinstance(v, str) and "\n" in v:
                    rows.append(f"{pad}{k}: {dumped}")
                else:
                    rows.append(f"{pad}{k}: {dumped}")
        return "\n".join(rows)
    return _quote(str(value))
