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
                    if isinstance(v, dict) and v:
                        dumped = to_yaml(v, indent + 2)
                        rest.append(f"{pad}  {k}:\n{dumped}")
                    elif isinstance(v, list) and v:
                        dumped = to_yaml(v, indent + 2)
                        rest.append(f"{pad}  {k}:\n{dumped}")
                    else:
                        dumped = to_yaml(v, indent + 1)
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


def parse_yaml(src: str) -> Any:
    """Parse the YAML subset this plugin emits. No PyYAML required."""
    tokens: list[tuple[int, str]] = []
    for line in src.replace("\r\n", "\n").split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        tokens.append((indent, line[indent:]))
    if not tokens:
        return {}
    value, _ = _parse_block(tokens, 0, tokens[0][0])
    return value


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if text in ("|", ">", ">-", "|-"):
        return text
    if text == "[]":
        return []
    if text == "{}":
        return {}
    if text in ("null", "~"):
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    if re.match(r"^-?\d+$", text):
        return int(text)
    if re.match(r"^-?\d+\.\d+$", text):
        return float(text)
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1].replace('\\"', '"')
    return text


def _parse_block(tokens: list[tuple[int, str]], start: int, parent_indent: int) -> tuple[Any, int]:
    if start >= len(tokens):
        return None, start
    indent, text = tokens[start]
    if indent < parent_indent:
        return None, start
    if text.startswith("- "):
        items: list[Any] = []
        i = start
        dash_indent = indent
        while i < len(tokens) and tokens[i][0] == dash_indent and tokens[i][1].startswith("- "):
            rest = tokens[i][1][2:]
            if ":" in rest:
                obj_tokens = [(dash_indent + 2, rest)]
                j = i + 1
                while j < len(tokens) and tokens[j][0] > dash_indent:
                    obj_tokens.append(tokens[j])
                    j += 1
                parsed, _ = _parse_map(obj_tokens, 0, dash_indent + 2)
                items.append(parsed)
                i = j
            else:
                items.append(_parse_scalar(rest))
                i += 1
        return items, i
    return _parse_map(tokens, start, indent)


def _parse_map(tokens: list[tuple[int, str]], start: int, indent: int) -> tuple[dict[str, Any], int]:
    obj: dict[str, Any] = {}
    i = start
    while i < len(tokens) and tokens[i][0] >= indent and not tokens[i][1].startswith("- "):
        if tokens[i][0] != indent:
            break
        colon = tokens[i][1].find(":")
        if colon < 0:
            break
        key = tokens[i][1][:colon].strip()
        raw = tokens[i][1][colon + 1 :]
        trimmed = raw.strip()
        if trimmed == "" or trimmed in ("|", "|-"):
            if trimmed.startswith("|"):
                lines: list[str] = []
                j = i + 1
                while j < len(tokens) and tokens[j][0] > indent:
                    lines.append(" " * (tokens[j][0] - indent - 2) + tokens[j][1])
                    j += 1
                obj[key] = "\n".join(lines)
                i = j
            else:
                child, nxt = _parse_block(tokens, i + 1, indent + 1)
                obj[key] = {} if child is None else child
                i = nxt
        else:
            obj[key] = _parse_scalar(raw)
            i += 1
    return obj, i

