#!/usr/bin/env python3
"""Deterministic AGER → Orca generator. Stdlib only."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ir import HOST_CLI, HOST_LABEL, AgerGraph, Agent, load_bundle
from layout import dump_json, to_yaml, write
from validate import NAMED_ROLE_RE, validate_graph, validate_project

PLUGIN_VERSION = "0.1.0"

CONCEPT_MAP = [
    ("AgentGraph / AgentGraphModule", "Orca Project / Run", "Top-level orchestration unit. Emits orca-project.yaml."),
    ("OrchestratorAgent", "Lead session (named, no isolated worktree)", "Plans, spawns, re-plans. Example: Claude-Plan-Drafter."),
    ("WorkerAgent", "Named agent in isolated git worktree", "orca worktree create --name wt-<host> --agent <cli>"),
    ("JudgeAgent", "Dedicated judge worktree or post-run reviewer", "Writes critique / judgment markdown. Reviews the other implementations."),
    ("SynthesizerAgent", "Mediator / idea-steal step", "Picks a winner and instructs it to steal the best ideas."),
    ("RouterAgent", "Conditional ControlEdge → stage routing", "Task DAG edges in orca orchestration."),
    ("GuardrailAgent", "Pre/post schema validation + ToolRule", "Final-Spec-Reviewer checks the winner against the original plan."),
    ("HumanGate", "orca orchestration gate-create + merge gate", "Optional mobile notification and PR merge approval."),
    ("FanOut / ParallelGroup", "Parallel worktrees fan-out", "One worktree per parallel agent. Names stay unique."),
    ("FanIn", "Comparison / judgment stage", "Judges read sibling worktrees and write score files."),
    ("LoopControl / LoopPolicy", "Task budget, max_turns, deadline, no_progress", "Hosts do not meter USD; the run script tracks an estimate and stops."),
    ("ScratchPad", "Shared plan.md + critique files + artifacts/", "docs/planning/<feature>-<date>.md is the durable plan."),
    ("Tool + ToolRule", "Agent CLI tools + Orca CLI", "worktree create, snapshot, terminal send, orchestration send."),
    ("Run / Trigger", "orca orchestration run-create", "Triggered by prompt or ticket: start new feature: <description>."),
    ("Rubric / Judgment", "Judge critique files + final score", "artifacts/judgments/judge-<host>.md"),
    ("Named roles", "<Host>-<Role> session titles", "Remote-control list stays intelligible. Policy: rename | disable."),
]


def slug(value: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return out or "orca-project"


def title_host(host: str) -> str:
    return HOST_LABEL.get(host, host[:1].upper() + host[1:])


def title_role(role: str) -> str:
    parts = [p for p in re.split(r"[-_/]+", role) if p]
    return "-".join(p[:1].upper() + p[1:] for p in parts)


def named_role(host: str, role: str, prefix: str = "") -> str:
    base = f"{title_host(host)}-{title_role(role)}"
    if not prefix.strip():
        return base
    return f"{prefix.rstrip('-')}-{base}"


def orca_name_for(agent: Agent, prefix: str = "") -> str:
    if agent.title and NAMED_ROLE_RE.match(agent.title) and not prefix:
        return agent.title
    if agent.title and NAMED_ROLE_RE.match(agent.title) and prefix:
        clean = prefix.rstrip("-")
        if agent.title.startswith(f"{clean}-"):
            return agent.title
        return f"{clean}-{agent.title}"
    return named_role(agent.host, agent.role, prefix)


def agent_cli_for(host: str) -> str:
    return HOST_CLI.get(host, host)


def _agent_by_id(graph: AgerGraph, agent_id: str) -> Agent | None:
    return next((a for a in graph.agents if a.id == agent_id), None)


def build_project(
    graph: AgerGraph,
    *,
    remote_control: str | None = None,
    name_prefix: str | None = None,
) -> dict[str, Any]:
    policy = remote_control or graph.remote_control
    prefix = name_prefix if name_prefix is not None else graph.name_prefix
    agents: list[dict[str, Any]] = []
    for agent in graph.agents:
        name = orca_name_for(agent, prefix)
        agents.append(
            {
                "name": name,
                "host": agent.host,
                "agent": agent_cli_for(agent.host),
                "role": agent.role,
                "ager_id": agent.id,
                "type": agent.type,
                "worktree": agent.worktree,
                "prompt": f"agents/{name}/SYSTEM.md",
                "reads": agent.reads,
                "writes": agent.writes,
                "input_schema": agent.input_schema.path,
                "output_schema": agent.output_schema.path,
                "stage": agent.stage,
                "parallel_group": agent.parallel_group,
                "judge_targets": [
                    orca_name_for(target, prefix) if (target := _agent_by_id(graph, tid)) else tid
                    for tid in agent.judge_targets
                ],
                "budget": {
                    "max_turns": agent.max_turns or graph.loop.max_turns,
                    "timeout_ms": agent.timeout_ms or 180_000,
                },
                "instructions": agent.instructions,
            }
        )

    stages = []
    for stage in graph.stages:
        stages.append(
            {
                "id": stage.id,
                "title": stage.title,
                "parallel": stage.parallel,
                "isolated_worktrees": stage.isolated_worktrees,
                "agents": [
                    orca_name_for(node, prefix) if (node := _agent_by_id(graph, aid)) else aid
                    for aid in stage.agents
                ],
            }
        )

    gates: list[dict[str, Any]] = []
    if graph.gate:
        after = _agent_by_id(graph, graph.gate.after) or graph.agents[-1]
        gates.append(
            {
                "id": graph.gate.id,
                "type": "human",
                "after": orca_name_for(after, prefix),
                "question": graph.gate.question,
                "options": graph.gate.options,
                "action": graph.gate.action,
            }
        )

    return {
        "apiVersion": "orca.stably.ai/v1",
        "kind": "Project",
        "metadata": {
            "name": slug(graph.id),
            "title": graph.title,
            "ager_id": graph.id,
            "ager_version": graph.ager_version,
            "generated_by": f"orca-ager@{PLUGIN_VERSION}",
        },
        "spec": {
            "objective": graph.objective,
            "remote_control": {"policy": policy, "name_prefix": prefix},
            "artifacts": {
                "planning_dir": "docs/planning",
                "critiques_dir": "artifacts/critiques",
                "judgments_dir": "artifacts/judgments",
                "shared_dir": "artifacts",
            },
            "loop": {
                "max_turns": graph.loop.max_turns,
                "price_budget_usd": graph.loop.price_budget_usd,
                "deadline_ms": graph.loop.deadline_ms,
                "check_order": graph.loop.check_order,
                "on_goal": graph.loop.on_goal,
                "on_exhaust": graph.loop.on_exhaust,
            },
            "stages": stages,
            "agents": agents,
            "gates": gates,
        },
    }


def remote_control_json(project: dict[str, Any]) -> str:
    spec = project["spec"]
    agents = spec["agents"]
    if spec["remote_control"]["policy"] == "disable":
        return dump_json(
            {
                "policy": "disable",
                "note": "Do not expose these sessions on Claude Code remote-control. Named panes stay local to Orca.",
                "agents": [a["name"] for a in agents],
            }
        )
    return dump_json(
        {
            "policy": "rename",
            "map": {a["ager_id"]: a["name"] for a in agents},
            "titles": [
                {"name": a["name"], "host": a["host"], "worktree": a["worktree"], "stage": a["stage"]}
                for a in agents
            ],
        }
    )


def compile_report(graph: AgerGraph, project: dict[str, Any]) -> str:
    agents = project["spec"]["agents"]
    rows = "\n".join(
        f"| `{a['ager_id']}` | {a['type']} | **{a['name']}** | {a['worktree'] or 'lead session'} |"
        for a in agents
    )
    map_rows = "\n".join(f"| {ager} | {orca} |" for ager, orca, _note in CONCEPT_MAP)
    entry = next((a["name"] for a in agents if a["ager_id"] == graph.entry), graph.entry)
    loop = project["spec"]["loop"]
    return f"""# COMPILE.md — {graph.title}

Generated by orca-ager@{PLUGIN_VERSION} from AGER {graph.ager_version}.

Entry: `{entry}`
Remote control: **{project['spec']['remote_control']['policy']}**
LoopPolicy: {' → '.join(loop['check_order'])}
max_turns={loop['max_turns']}  price=${loop['price_budget_usd']}  deadline_ms={loop['deadline_ms']}

## Named agents

| AGER id | Type | Orca name | Worktree |
| --- | --- | --- | --- |
{rows}

## Concept map used

| AGER | Orca |
| --- | --- |
{map_rows}

## Run

```bash
bash scripts/run-feature.sh "start new feature: <description>"
```

Do not invent extra agents. Honor LoopPolicy. Isolated parallel stages must not share a worktree.
"""


def run_script(project: dict[str, Any]) -> str:
    objective = str(project["spec"]["objective"]).replace('"', '\\"')
    lines = [
        "#!/usr/bin/env bash",
        "# Generated by orca-ager — do not freehand. Re-emit after graph changes.",
        "set -euo pipefail",
        f'OBJECTIVE="${{1:-{objective}}}"',
        'command -v orca >/dev/null || { echo "orca CLI not on PATH"; exit 1; }',
        'command -v jq >/dev/null || { echo "jq is required"; exit 1; }',
        "",
        'RUN_ID=$(orca orchestration run-create --objective "$OBJECTIVE" --json | jq -r .id)',
        'echo "run $RUN_ID"',
        "",
    ]
    by_name = {a["name"]: a for a in project["spec"]["agents"]}
    for stage in project["spec"]["stages"]:
        lines.append(f"# --- {stage['title']} ({stage['id']}) ---")
        for name in stage["agents"]:
            agent = by_name.get(name)
            if not agent:
                continue
            var = "TASK_" + agent["ager_id"].replace("-", "_").upper()
            lines.append(
                f'{var}=$(orca orchestration task-create --spec "$OBJECTIVE" --task-title "{agent["name"]}" --json | jq -r .id)'
            )
            if agent.get("worktree"):
                lines.append(
                    f"orca worktree create --name {agent['worktree']} --agent {agent['agent']} --json >/dev/null"
                )
                lines.append(
                    f'orca orchestration worker-start --task "${var}" --worktree new-top-level --name {agent["name"]} --agent {agent["agent"]} --json'
                )
            else:
                lines.append(
                    f'orca orchestration worker-start --task "${var}" --worktree current --name {agent["name"]} --agent {agent["agent"]} --json'
                )
            lines.append(f'orca terminal send --text "$(cat {agent["prompt"]})" --enter --json >/dev/null || true')
        if stage.get("parallel"):
            lines.append("orca orchestration check --wait --types worker_done,escalation,question --timeout-ms 900000 --json")
        else:
            lines.append("orca orchestration check --wait --types worker_done --timeout-ms 900000 --json")
        lines.append("")
    for gate in project["spec"].get("gates") or []:
        question = str(gate["question"]).replace('"', '\\"')
        options = json.dumps(gate["options"])
        lines.append(f"# HumanGate: {gate['id']}")
        lines.append(
            f"orca orchestration gate-create --task \"$RUN_ID\" --question \"{question}\" --options '{options}' --json"
        )
    lines.append('echo "orca-ager run complete: $RUN_ID"')
    return "\n".join(lines) + "\n"


def handoffs(project: dict[str, Any]) -> str:
    rows = []
    for agent in project["spec"]["agents"]:
        reads = ", ".join(agent.get("reads") or []) or "—"
        writes = ", ".join(agent.get("writes") or []) or "—"
        rows.append(f"| **{agent['name']}** | {reads} | {writes} |")
    body = "\n".join(rows)
    return f"""# Stage hand-off contracts

Plan files live under `docs/planning/`. Critiques and judgments live under `artifacts/`.

| Agent | Reads | Writes |
| --- | --- | --- |
{body}
"""


def system_prompt(agent: dict[str, Any], graph: AgerGraph, project: dict[str, Any]) -> str:
    tree = (
        f"Isolated git worktree: `{agent['worktree']}`."
        if agent.get("worktree")
        else "Lead / shared session. Do not create a worktree."
    )
    judges = ""
    if agent.get("judge_targets"):
        names = ", ".join(f"**{n}**" for n in agent["judge_targets"])
        judges = f"You review: {names}. Never score yourself."
    policy = project["spec"]["remote_control"]["policy"]
    remote = (
        "Remote-control listing is disabled for this session."
        if policy == "disable"
        else f"Remote-control title: **{agent['name']}**. Do not rename yourself."
    )
    order = " → ".join(graph.loop.check_order)
    return f"""---
name: {agent['name']}
host: {agent['host']}
role: {agent['role']}
ager_id: {agent['ager_id']}
---

# {agent['name']}

{agent['instructions']}

{tree}
{judges}
{remote}

InputSchema: `{agent['input_schema']}`
OutputSchema: `{agent['output_schema']}`
LoopPolicy check order: {order}
Stop if max_turns={agent['budget']['max_turns']} or timeout_ms={agent['budget']['timeout_ms']}.

Write only the contracted files. Do not invent agents.
"""


def emit(
    graph: AgerGraph,
    out: Path,
    *,
    remote_control: str | None = None,
    name_prefix: str | None = None,
) -> list[Path]:
    graph_check = validate_graph(graph)
    if not graph_check.ok:
        raise SystemExit("\n".join(i.message for i in graph_check.errors))
    project = build_project(graph, remote_control=remote_control, name_prefix=name_prefix)
    project_check = validate_project(project)
    if not project_check.ok:
        raise SystemExit("\n".join(i.message for i in project_check.errors))

    files: dict[str, str] = {
        "orca-project.yaml": f"# Generated by orca-ager@{PLUGIN_VERSION}\n{to_yaml(project)}\n",
        "remote-control.json": remote_control_json(project),
        "COMPILE.md": compile_report(graph, project),
        "handoffs.md": handoffs(project),
        "scripts/run-feature.sh": run_script(project),
        "docs/planning/.gitkeep": "",
        "artifacts/critiques/.gitkeep": "",
        "artifacts/judgments/.gitkeep": "",
        "artifacts/implementations/.gitkeep": "",
    }
    by_id = {a["ager_id"]: a for a in project["spec"]["agents"]}
    for agent in graph.agents:
        compiled = by_id[agent.id]
        files[compiled["prompt"]] = system_prompt(compiled, graph, project)
        files[f"agents/{compiled['name']}/contract.json"] = dump_json(
            {
                "name": compiled["name"],
                "input": agent.input_schema.schema,
                "output": agent.output_schema.schema,
                "reads": compiled["reads"],
                "writes": compiled["writes"],
            }
        )
        files[agent.input_schema.path] = dump_json(agent.input_schema.schema)
        files[agent.output_schema.path] = dump_json(agent.output_schema.schema)

    written = [write(out, rel, content) for rel, content in sorted(files.items())]
    script = out / "scripts" / "run-feature.sh"
    if script.exists():
        script.chmod(script.stat().st_mode | 0o111)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(prog="orca-ager")
    parser.add_argument("--bundle", type=Path, help="AGER bundle directory (defaults to the sample graph)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--remote-control", choices=["rename", "disable"])
    parser.add_argument("--name-prefix", default=None)
    args = parser.parse_args()
    written = emit(
        load_bundle(args.bundle),
        args.out,
        remote_control=args.remote_control,
        name_prefix=args.name_prefix,
    )
    print(f"wrote {len(written)} files to {args.out}")
    for path in written:
        print(" ", path)


if __name__ == "__main__":
    main()
