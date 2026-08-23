"""Official Orca peer skills used by the AGER translator.

orca-cli        worktrees, terminals, handoffs, snapshots, embedded browser
orchestration   Runs, Tasks, workers, DAGs, gates, coordinator loops

Discovery stubs live in skills/orca-cli and skills/orchestration. The live
command guide is always `orca skills get <topic>` so flags cannot drift.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"

PEER_SKILLS: list[dict[str, str]] = [
    {
        "name": "orca-cli",
        "source": "https://github.com/stablyai/orca",
        "install_npx": "npx skills add https://github.com/stablyai/orca --skill orca-cli --global",
        "install_orca": "orca skills install --skill orca-cli --skill orchestration",
        "load": "orca skills get orca-cli",
        "use": "Worktrees, terminals, folder contexts, full handoffs, snapshots, automations, embedded browser. Prefer over raw git worktree.",
        "primary_for": "isolated worktree agents (implementers, judges) and any handoff",
    },
    {
        "name": "orchestration",
        "source": "https://github.com/stablyai/orca",
        "install_npx": "npx skills add https://github.com/stablyai/orca --skill orchestration --global",
        "install_orca": "orca skills install --skill orca-cli --skill orchestration",
        "load": "orca skills get orchestration --full",
        "use": "Runs, Tasks, supervised workers, worker_done/escalation waits, task DAGs, decision gates, coordinator loops. Maps onto plan → review → implement → judge → mediate.",
        "primary_for": "Orca-Coordinator and lead-session stages (draft, review, refine, mediate, spec-review)",
    },
]

SKILL_PREAMBLE = """## Orca skills (required)

Load and prefer the **orca-cli** and **orchestration** skills. Call `orca skills get orca-cli` and `orca skills get orchestration --full` before mutating worktrees or orchestration state. Use Orca worktrees for every parallel implementer and judge. Use orchestration primitives for the overall DAG and mediator step.

- Resolve the executable once: `ORCA_CLI_COMMAND` → `orca-dev` → `orca-ide` on Linux outside an Orca terminal → `orca`. Never run bare `orca` on Linux outside Orca — that is the GNOME screen reader.
- Prefer `--json`. Confirm the app with `status --json` (`open --json` if needed).
- Do not guess flags from memory. The stubs are discovery only; the binary serves the live guide.
- Prefer orca-cli over raw `git worktree`, ad-hoc PTYs, or Playwright for Orca-managed state.
"""


def skills_for(agent: dict[str, Any]) -> dict[str, Any]:
    """Bind peer skills to a compiled agent. Everyone loads both; primary differs."""
    if agent.get("worktree"):
        return {
            "primary": "orca-cli",
            "required": ["orca-cli", "orchestration"],
            "why": "Isolated git worktree. Prefer orca-cli for worktree create / terminal / handoff. Use orchestration to send worker_done or ask.",
        }
    if agent.get("type") in {"OrchestratorAgent", "SynthesizerAgent", "GuardrailAgent"}:
        return {
            "primary": "orchestration",
            "required": ["orchestration", "orca-cli"],
            "why": "Lead session on the coordinator loop. Load orchestration --full before dispatching, waiting, or opening a gate.",
        }
    return {
        "primary": "orchestration",
        "required": ["orchestration", "orca-cli"],
        "why": "Named worker on the DAG. Load live guides before any Orca command. Use orca-cli for terminals.",
    }


def load_stub(name: str) -> str:
    path = SKILLS_ROOT / name / "SKILL.md"
    return path.read_text(encoding="utf-8")


def orca_skills_doc() -> str:
    return """# Orca skills for this compiled project

AGER compiled this fleet to run **inside Orca ADE**. Two peer skills from [stablyai/orca](https://github.com/stablyai/orca) are required. They are discovery stubs — load the live, version-matched guide from the running binary before any command.

## Install

```bash
npx skills add https://github.com/stablyai/orca --skill orca-cli --global
npx skills add https://github.com/stablyai/orca --skill orchestration --global
```

```bash
orca skills install --skill orca-cli --skill orchestration
# optional: --agent claude-code,codex,grok
# optional: --local   (this project only)
```

## Load (every session, before mutating state)

```bash
orca skills get orca-cli
orca skills get orchestration --full
```

Use `--json` when an agent needs deterministic output.

## When to use which

| Skill | Use for |
| --- | --- |
| **orca-cli** | Named worktrees (`wt-claude`, `wt-grok`, `wt-codex`), terminals, full handoffs, snapshots, embedded browser. Prefer over raw `git worktree`. |
| **orchestration** | `run-create`, `task-create`, `worker-start --name <Host>-<Role>`, `check --wait --types worker_done,escalation,question`, `gate-create`, coordinator loops. This is the plan → review → implement → judge → mediate DAG. |

The generated coordinator (`agents/Orca-Coordinator/SYSTEM.md`) drives the DAG with the orchestration skill. Isolated implementers and judges use orca-cli for their worktrees and send `worker_done` on the orchestration bus.

## Verify

```bash
orca status --json
orca skills list
orca skills get orca-cli
```

Linux outside an Orca-managed terminal: use `orca-ide`, never bare `orca` (GNOME screen reader).
"""


def coordinator_prompt(project: dict[str, Any]) -> str:
    spec = project["spec"]
    stage_lines: list[str] = []
    by_name = {a["name"]: a for a in spec["agents"]}
    for stage in spec["stages"]:
        kind = "parallel" if stage.get("parallel") else "sequential"
        trees = "isolated named worktrees" if stage.get("isolated_worktrees") else "lead / current worktree"
        stage_lines.append(f"### {stage['id']} — {stage['title']} ({kind}, {trees})")
        for name in stage["agents"]:
            agent = by_name.get(name) or {}
            wt = agent.get("worktree")
            cli = agent.get("agent", "claude")
            skill = (agent.get("skills") or {}).get("primary", "orchestration")
            if wt:
                stage_lines.append(
                    f"- **{name}** (`{cli}`) — orca-cli `worktree create --name {wt} --agent {cli}`, "
                    f"then orchestration `task-create --task-title {name}` + "
                    f"`worker-start --task <id> --worktree {wt} --name {name} --agent {cli}`. "
                    f"Primary skill: {skill}."
                )
            else:
                stage_lines.append(
                    f"- **{name}** (`{cli}`) — orchestration `task-create --task-title {name}` + "
                    f"`worker-start --task <id> --worktree current --name {name} --agent {cli}`. "
                    f"Primary skill: {skill}."
                )
        wait = (
            "`check --wait --types worker_done,escalation,question`"
            if stage.get("parallel")
            else "`check --wait --types worker_done`"
        )
        stage_lines.append(f"- Wait: orchestration {wait} using the live guide's timeout flags.")
        stage_lines.append("")
    gates = spec.get("gates") or []
    gate_block = "No HumanGate."
    if gates:
        rows = []
        for gate in gates:
            options = ", ".join(gate.get("options") or [])
            rows.append(
                f"- After **{gate.get('after')}**: `gate-create` question `{gate.get('question')}` options [{options}] action `{gate.get('action')}`."
            )
        gate_block = "\n".join(rows)
    stages_md = "\n".join(stage_lines).rstrip()
    return f"""---
name: Orca-Coordinator
host: orca
role: Coordinator
ager_id: orca-coordinator
---

# Orca-Coordinator

You drive the compiled AGER graph as an Orca **orchestration** DAG. You do not implement the feature and you do not invent agents.

{SKILL_PREAMBLE}

Primary skill: **orchestration** (`orca skills get orchestration --full`). Use **orca-cli** only to create named worktrees and send the SYSTEM.md prompt into each worker terminal.

Read `orca-project.yaml`. Honor `<Host>-<Role>` names and remote-control policy **{spec['remote_control']['policy']}**. Isolated parallel stages must not share a worktree.

## Dispatch recipe (orchestration primitives, not custom glue)

1. `status --json` (or `open --json`). Load both live guides.
2. `orchestration run-create --objective "<objective>" --json`
3. For each stage below, in order:
   - `task-create --spec "<objective>" --task-title <Name> --json` for every named agent
   - Isolated agents: orca-cli `worktree create --name <wt> --agent <cli>` then `worker-start --worktree <wt> --name <Name> --agent <cli>`
   - Lead-session agents: `worker-start --worktree current --name <Name> --agent <cli>`
   - `terminal send` the matching `agents/<Name>/SYSTEM.md` (orca-cli)
   - Wait with `orchestration check --wait` as noted
4. HumanGate last.

Workers report with `orchestration send --type worker_done`. On `escalation` or `question`, decide or forward to the gate. Do not raw-`git worktree`. Do not skip named roles.

## Stages

{stages_md}

## HumanGate

{gate_block}

Objective: `{spec['objective']}`
"""


RESOLVE_ORCA_BASH = r'''resolve_orca_bin() {
  if [ -n "${ORCA_CLI_COMMAND:-}" ]; then
    printf '%s\n' "$ORCA_CLI_COMMAND"
    return
  fi
  if [ -n "${ORCA_DEV_REPO_ROOT:-}" ]; then
    printf '%s\n' "orca-dev"
    return
  fi
  case "$(uname -s)" in
    Linux)
      if [ -n "${ORCA_SESSION:-}" ] || [ -n "${ORCA_MANAGED:-}" ]; then
        printf '%s\n' "orca"
      else
        # Never bare `orca` on Linux outside an Orca terminal (GNOME screen reader).
        printf '%s\n' "orca-ide"
      fi
      ;;
    *)
      printf '%s\n' "orca"
      ;;
  esac
}
'''
