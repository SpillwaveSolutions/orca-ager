"""Multi-host plugin manifests (Claude, Grok, Codex, Cursor, Agent Plugins 1.0)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VERSION = "0.2.0"
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
AUTHOR = {"name": "Rick Hightower", "url": "https://github.com/RichardHightower"}
NAME = "orca-ager"
DESCRIPTION = (
    "Translate a validated AGER/OKF AgentGraph into Orca ADE orchestration — "
    "named worktree agents, parallel fan-out, orca-cli + orchestration skills, remote-control rename or disable."
)
HOMEPAGE = "https://github.com/SpillwaveSolutions/orca-ager"
KEYWORDS = [
    "ager",
    "okf",
    "orca",
    "ade",
    "stably",
    "worktree",
    "multi-agent",
    "translator",
    "orca-cli",
    "orchestration",
    "claude-code",
    "grok-build",
    "codex",
    "cursor",
    "agent-plugins",
    "worklog",
    "wiki-ticket-sdd",
]
COMMAND = "/orca-compile"
BRAND = "#07080a"


def write(out: Path, rel: str, content: str) -> Path:
    dest = out / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    dest.write_text(content, encoding="utf-8")
    return dest


def dump(obj: Any) -> str:
    return json.dumps(obj, indent=2) + "\n"


def identity() -> dict[str, Any]:
    return {
        "$schema": SCHEMA,
        "name": NAME,
        "version": VERSION,
        "description": DESCRIPTION,
        "author": AUTHOR,
        "homepage": HOMEPAGE,
        "repository": HOMEPAGE,
        "license": "MIT",
        "keywords": KEYWORDS,
    }


def write_host_matrix(out: Path) -> list[Path]:
    written: list[Path] = []
    ident = identity()
    claude = {k: v for k, v in ident.items() if k != "$schema"}
    written.append(write(out, "plugin.json", dump(ident)))
    written.append(write(out, ".claude-plugin/plugin.json", dump(claude)))
    market = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": f"{NAME}-marketplace",
        "description": DESCRIPTION,
        "owner": {"name": "Rick Hightower", "url": "https://github.com/RichardHightower"},
        "plugins": [
            {
                "name": NAME,
                "source": "./",
                "description": DESCRIPTION,
                "version": VERSION,
                "author": {"name": "Rick Hightower"},
                "homepage": HOMEPAGE,
                "repository": HOMEPAGE,
                "license": "MIT",
                "keywords": KEYWORDS,
                "category": "productivity",
            }
        ],
    }
    written.append(write(out, ".claude-plugin/marketplace.json", dump(market)))
    written.append(
        write(
            out,
            "marketplace.json",
            dump(
                {
                    "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
                    "name": f"{NAME}-marketplace",
                    "owner": {"name": "Rick Hightower", "url": "https://github.com/RichardHightower"},
                    "plugins": [
                        {"name": NAME, "source": "./", "description": DESCRIPTION, "version": VERSION}
                    ],
                }
            ),
        )
    )
    written.append(
        write(
            out,
            ".grok-plugin/marketplace.json",
            dump(
                {
                    "name": f"{NAME}-marketplace",
                    "description": f"{DESCRIPTION} Grok Build loads the Claude layout with zero config.",
                    "version": VERSION,
                    "plugins": [
                        {
                            "name": NAME,
                            "source": ".",
                            "description": DESCRIPTION,
                            "version": VERSION,
                            "compatibility": {"claude_plugin": True, "zero_config": True},
                            "depends_on": [
                                {
                                    "plugin": "okf-agent-graph",
                                    "repository": "https://github.com/SpillwaveSolutions/okf-agent-graph",
                                }
                            ],
                            "repository": HOMEPAGE,
                        }
                    ],
                }
            ),
        )
    )
    written.append(
        write(
            out,
            ".codex-plugin/plugin.json",
            dump(
                {
                    "name": NAME,
                    "version": VERSION,
                    "description": DESCRIPTION,
                    "author": AUTHOR,
                    "homepage": HOMEPAGE,
                    "repository": HOMEPAGE,
                    "license": "MIT",
                    "keywords": KEYWORDS,
                    "skills": "./skills/",
                    "interface": {
                        "displayName": NAME,
                        "shortDescription": DESCRIPTION,
                        "longDescription": DESCRIPTION,
                        "developerName": "Spillwave Solutions",
                        "category": "Developer Tools",
                        "capabilities": ["Read", "Write"],
                        "websiteURL": HOMEPAGE,
                        "defaultPrompt": [
                            f"Run {COMMAND} on the AGER bundle in this workspace.",
                            "Compile the graph. Do not author a new AGER graph.",
                        ],
                        "brandColor": BRAND,
                    },
                }
            ),
        )
    )
    written.append(
        write(
            out,
            ".cursor-plugin/plugin.json",
            dump(
                {
                    "name": NAME,
                    "version": VERSION,
                    "description": DESCRIPTION,
                    "author": {"name": "Rick Hightower"},
                    "homepage": HOMEPAGE,
                    "repository": HOMEPAGE,
                    "license": "MIT",
                    "keywords": KEYWORDS + (["cursor"] if "cursor" not in KEYWORDS else []),
                    "skills": "skills/",
                    "rules": ".cursor/rules/",
                    "commands": "commands/",
                }
            ),
        )
    )
    return written


def write_cursor_docs(out: Path) -> list[Path]:
    written: list[Path] = []
    written.append(
        write(
            out,
            "docs/CURSOR.md",
            f"""# Cursor — binding this plugin

Cursor is a first-class host. This is **not** a second copy of the skills.
Same `skills/`, same `scripts/emit.py`, same compile rules.

## How Cursor loads this pack

| Layer | What we ship | Where |
|-------|----------------|-------|
| Agent Skills | Existing `SKILL.md` files | `skills/` |
| Agent Plugins 1.0 | Root `plugin.json` | repo root |
| Cursor Plugins | Rules + skill pointer | `.cursor-plugin/plugin.json` |
| MCP | Not in this pack | deferred |

Cursor also reads `.claude/skills/` and `.codex/skills/` for compatibility.

## Install (local Cursor)

```text
/plugin marketplace add SpillwaveSolutions/{NAME}
/plugin install {NAME}
```

Or open this repo and load it as a local plugin.

Root `plugin.json` already declares the Agent Plugins 1.0 schema, so Cursor
loads skills without a rewrite.

## Cloud Cursor

A Grok Bot / Cursor cloud session usually opens the **workspace**, not this
plugin cache. The cloud agent sees `AGENTS.md` and `scripts/emit.py` if they
are present. Prefer the script:

```bash
python3 scripts/emit.py --bundle sample-ager --out ./generated
```

Do not freehand the emitted tree. Do not invent agents that are not in the graph.

## Rules

`.cursor/rules/ager-translator.mdc` is always-on when this repo is the Cursor
workspace.

## Related

- [HOSTS.md](HOSTS.md)
- https://cursor.com/docs/plugins
- https://agent-plugins.org
""",
        )
    )
    written.append(
        write(
            out,
            "docs/HOSTS.md",
            f"""# Host matrix

`{NAME}` is one plugin, five install surfaces. Skills live once under `skills/`.

| Host | Manifest | Install |
| --- | --- | --- |
| Agent Plugins 1.0 | `plugin.json` | any host that reads agent-plugins.org |
| Claude Code | `.claude-plugin/plugin.json` + `marketplace.json` | `claude plugin marketplace add SpillwaveSolutions/{NAME}` |
| Grok Build | `.grok-plugin/marketplace.json` (Claude layout is zero-config) | drop into workspace / Claude marketplace |
| Codex | `.codex-plugin/plugin.json` | `codex plugin marketplace add SpillwaveSolutions/{NAME}` |
| Cursor | `.cursor-plugin/plugin.json` + `.cursor/rules/` | `/plugin install {NAME}` |

Command on Claude/Grok: `{COMMAND}`
Command on Codex: `$orca-compile`

Depends on `okf-agent-graph` for author/validate. This plugin only compiles.
Orca ADE is the runtime: https://github.com/stablyai/orca · https://www.onorca.dev/

Peer skills from the orca-ager plugin (required at runtime):

```bash
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill ager-to-orca --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orca-cli --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orchestration --global
orca skills get orca-cli
orca skills get orchestration --full
```

Worktrees and handoffs use **orca-cli**. The plan → review → implement → judge → mediate DAG uses **orchestration**. Never raw `git worktree`.
""",
        )
    )
    written.append(
        write(
            out,
            "hosts/cursor/SKILL.md",
            f"""---
name: cursor-{NAME}
description: Bind a Cursor agent to {NAME}. Compile AGER graphs into Orca ADE. Do not author graphs.
---

# Cursor / {NAME}

Follow `docs/CURSOR.md` and `docs/HOSTS.md`.

1. Identity: `cursor/{NAME}`.
2. Local Cursor may `/plugin install {NAME}`.
3. Compile with `python3 scripts/emit.py --bundle <AGER> --out <OUT>`.
4. Never invent agents. Never write a new AGER graph (that is `okf-agent-graph`).
""",
        )
    )
    written.append(
        write(
            out,
            ".cursor/rules/ager-translator.mdc",
            """---
description: AGER translator rules for Cursor agents
alwaysApply: true
---

You are compiling a validated AGER/OKF AgentGraph into Orca ADE. You are not authoring one.

1. Prefer `python3 scripts/emit.py --bundle <AGER> --out <OUT>`. Do not freehand the tree.
2. Do not invent agents, tools, or edges that are not in the graph.
3. Honor LoopPolicy check order: goal, deadline, price, max_turns, no_progress.
4. Every generated Orca agent must be named `<Host>-<Role>` (e.g. Claude-Plan-Drafter).
5. Parallel isolated stages get distinct git worktrees via **orca-cli**, never raw `git worktree`. Fail on overlap.
6. Remote-control policy is `rename` (default) or `disable`. Never leave anonymous panes.
7. Every SYSTEM.md must instruct the agent to `orca skills get orca-cli` and `orca skills get orchestration --full` before mutating ADE state.
8. The stage DAG (plan → review → implement → judge → mediate → gate) is an **orchestration** coordinator loop.
9. If `okf-agent-graph` / `ager-validate` is available, validate first. If it fails, stop.
10. Never claim production-ready without tests. Hosts do not meter USD; document the budget and stop.
11. Same skills serve Claude Code, Grok Build, Codex, Cursor, and Agent Plugins 1.0.
""",
        )
    )
    return written


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    written = write_host_matrix(root)
    written.extend(write_cursor_docs(root))
    print(f"wrote {len(written)} host files")
