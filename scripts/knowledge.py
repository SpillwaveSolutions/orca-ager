"""Optional OKF second-brain bind: KnowledgeBind, DecisionRecord, TicketLink."""

from __future__ import annotations

from typing import Any

RECORD_BY_ROLE = {
    "Plan-Reviewer": "DecisionRecord",
    "Judge": "DecisionRecord",
    "Mediator": "DecisionRecord",
    "Spec-Reviewer": "DecisionRecord",
    "Plan-Refiner": "TicketLink",
}


def normalize_root(root: str) -> str:
    text = (root or "second-brain").strip().rstrip("/")
    return f"{text}/"


def bind_spec(root: str) -> dict[str, Any]:
    bound = normalize_root(root)
    return {
        "apiVersion": "okf.spillwave.com/v1",
        "kind": "KnowledgeBind",
        "root": bound,
        "retrieval": {
            "read": "pull main. Do not write on main.",
            "write": "own worktree → branch → PR → merge",
        },
        "records": [
            {"type": "DecisionRecord", "source": "artifacts/judgments/", "dest": f"{bound}decisions/"},
            {"type": "DecisionRecord", "source": "artifacts/critiques/", "dest": f"{bound}decisions/critiques/"},
            {"type": "TicketLink", "source": "docs/planning/", "dest": f"{bound}tickets/"},
        ],
    }


def protocol_md(root: str) -> str:
    spec = bind_spec(root)
    rows = "\n".join(f"| `{r['type']}` | `{r['source']}` | `{r['dest']}` |" for r in spec["records"])
    return f"""# Second-brain / OKF bind

This project is bound to `{spec['root']}`.

## Write protocol

1. **Read** — pull `main`. Never write on `main`.
2. **Write** — own worktree → branch `okf/<record>` → PR → merge.
3. Critiques, judgments, and the winner decision are **DecisionRecords**.
4. The refined plan and HumanGate merge are **TicketLinks**.

## Record map

| Kind | From run artifacts | Into second-brain |
| --- | --- | --- |
{rows}
"""


def prompt_block(root: str, role: str) -> str:
    bound = normalize_root(root)
    kind = RECORD_BY_ROLE.get(role)
    if kind:
        return (
            f"Second-brain bind: `{bound}`. Your durable writes are **{kind}s**. "
            "Read from main only. To record, use your own worktree → branch → PR → merge. "
            "Never write second-brain files on main."
        )
    return (
        f"Second-brain bind: `{bound}`. Read from main only. "
        "Do not write second-brain files unless your contract names a DecisionRecord or TicketLink."
    )
