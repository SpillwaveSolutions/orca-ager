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
from knowledge import bind_spec, prompt_block, protocol_md
from layout import dump_json, to_yaml, write
from skills import (
    PEER_SKILLS,
    RESOLVE_ORCA_BASH,
    SKILL_PREAMBLE,
    coordinator_prompt,
    load_stub,
    orca_skills_doc,
    skills_for,
)
from validate import NAMED_ROLE_RE, validate_graph, validate_project

PLUGIN_VERSION = "0.2.0"

CONCEPT_MAP = [
    ("AgentGraph / AgentGraphModule", "Orca Project / Run", "Top-level orchestration unit. Emits orca-project.yaml."),
    ("OrchestratorAgent", "Lead session (named, no isolated worktree)", "Plans, spawns, re-plans. Example: Claude-Plan-Drafter. Primary skill: orchestration."),
    ("WorkerAgent", "Named agent in isolated git worktree (orca-cli)", "orca-cli worktree create --name wt-<host> --agent <cli>. Prefer over raw git worktree."),
    ("JudgeAgent", "Dedicated judge worktree or post-run reviewer", "Writes critique / judgment markdown. Reviews the other implementations."),
    ("SynthesizerAgent", "Mediator / idea-steal step", "Picks a winner and instructs it to steal the best ideas. Orchestration DAG step."),
    ("RouterAgent", "Conditional ControlEdge → stage routing", "Task DAG edges in orca orchestration."),
    ("GuardrailAgent", "Pre/post schema validation + ToolRule", "Final-Spec-Reviewer checks the winner against the original plan."),
    ("HumanGate", "orchestration gate-create + merge gate", "Optional mobile notification and PR merge approval. Load orchestration --full first."),
    ("FanOut / ParallelGroup", "Parallel named worktrees (orca-cli) + parallel workers (orchestration)", "One worktree per parallel agent. Names stay unique."),
    ("FanIn", "Comparison / judgment stage", "Judges read sibling worktrees and write score files."),
    ("LoopControl / LoopPolicy", "Task budget, max_turns, deadline, no_progress", "Hosts do not meter USD; the run script tracks an estimate and stops."),
    ("ScratchPad", "Shared plan.md + critique files + artifacts/", "docs/planning/<feature>-<date>.md is the durable plan."),
    ("Tool + ToolRule", "orca-cli skill", "worktree create, terminal send/wait, full handoff, snapshot. Prefer over raw git worktree."),
    ("Run / Trigger", "orchestration skill: run-create + task-create + worker-start", "Triggered by prompt or ticket: start new feature: <description>. Coordinator drives the DAG."),
    ("Rubric / Judgment", "Judge critique files + final score", "artifacts/judgments/judge-<host>.md"),
    ("Named roles", "<Host>-<Role> session titles", "Remote-control list stays intelligible. Policy: rename | disable."),
    ("Peer skills", "orca-cli + orchestration (stablyai/orca)", "Discovery stubs in skills/. Live guide: orca skills get orca-cli / orchestration --full."),
    ("Coordinator loop", "Orca-Coordinator", "Loads orchestration --full, then run-create → named workers → worker_done waits → gate-create."),
    ("KnowledgeBind / RetrievalBinding", "second-brain/ root + DecisionRecord / TicketLink", "Optional. Pull main to read. Own worktree → branch → PR to write."),
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
        agents[-1]["skills"] = skills_for(agents[-1])

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

    project = {
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
            "skills": PEER_SKILLS,
            "coordinator": {
                "name": "Orca-Coordinator",
                "prompt": "agents/Orca-Coordinator/SYSTEM.md",
                "skill": "orchestration",
            },
        },
    }
    if graph.knowledge_bind:
        project["spec"]["knowledge_bind"] = bind_spec(graph.knowledge_bind)
    return project


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

Peer skills: **orca-cli** (`orca skills get orca-cli`) and **orchestration** (`orca skills get orchestration --full`).
Coordinator: **Orca-Coordinator** drives the DAG. Isolated implementers/judges use orca-cli named worktrees, not raw git.

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
# install peer skills once
npx skills add https://github.com/stablyai/orca --skill orca-cli --global
npx skills add https://github.com/stablyai/orca --skill orchestration --global
bash scripts/run-feature.sh "start new feature: <description>"
```

Do not invent extra agents. Honor LoopPolicy. Isolated parallel stages must not share a worktree. Load live Orca skill guides before mutating ADE state.
"""


def run_script(project: dict[str, Any]) -> str:
    objective = str(project["spec"]["objective"]).replace('"', '\\"')
    lines = [
        "#!/usr/bin/env bash",
        "# Generated by orca-ager. Bootstrap + orchestration DAG. Re-emit after graph changes.",
        "# orca-cli        → named worktrees, terminals, handoffs (never raw git worktree)",
        "# orchestration   → run-create, task-create, worker-start --name, check --wait, gate-create",
        "set -euo pipefail",
        f'OBJECTIVE="${{1:-{objective}}}"',
        "",
        RESOLVE_ORCA_BASH.strip(),
        "",
        "ORCA_BIN=$(resolve_orca_bin)",
        'command -v "$ORCA_BIN" >/dev/null || { echo "Orca CLI not on PATH (resolved: $ORCA_BIN). Install Orca ADE or set ORCA_CLI_COMMAND."; exit 1; }',
        'command -v jq >/dev/null || { echo "jq is required"; exit 1; }',
        "",
        "# Confirm the ADE is up (from orca-cli / orchestration skill stubs).",
        '"$ORCA_BIN" status --json >/dev/null 2>&1 || "$ORCA_BIN" open --json >/dev/null',
        "",
        "# Peer skills. Stubs are discovery-only; load the live guide next.",
        '"$ORCA_BIN" skills install --skill orca-cli --skill orchestration >/dev/null 2>&1 || true',
        '"$ORCA_BIN" skills get orca-cli >/dev/null',
        '"$ORCA_BIN" skills get orchestration --full >/dev/null',
        "",
        'RUN_ID=$("$ORCA_BIN" orchestration run-create --objective "$OBJECTIVE" --json | jq -r .id)',
        'echo "run $RUN_ID"',
        "",
    ]
    by_name = {a["name"]: a for a in project["spec"]["agents"]}
    for stage in project["spec"]["stages"]:
        skill = "orca-cli worktrees + orchestration workers" if stage.get("isolated_worktrees") else "orchestration"
        lines.append(f"# --- {stage['title']} ({stage['id']}) via {skill} ---")
        for name in stage["agents"]:
            agent = by_name.get(name)
            if not agent:
                continue
            var = "TASK_" + agent["ager_id"].replace("-", "_").upper()
            lines.append(
                f'{var}=$("$ORCA_BIN" orchestration task-create --spec "$OBJECTIVE" --task-title "{agent["name"]}" --json | jq -r .id)'
            )
            if agent.get("worktree"):
                lines.append(
                    f'"$ORCA_BIN" worktree create --name {agent["worktree"]} --agent {agent["agent"]} --json >/dev/null'
                )
                lines.append(
                    f'"$ORCA_BIN" orchestration worker-start --task "${var}" --worktree {agent["worktree"]} --name {agent["name"]} --agent {agent["agent"]} --json'
                )
            else:
                lines.append(
                    f'"$ORCA_BIN" orchestration worker-start --task "${var}" --worktree current --name {agent["name"]} --agent {agent["agent"]} --json'
                )
            lines.append(
                f'"$ORCA_BIN" terminal send --text "$(cat {agent["prompt"]})" --enter --json >/dev/null || true'
            )
        if stage.get("parallel"):
            lines.append(
                '"$ORCA_BIN" orchestration check --wait --types worker_done,escalation,question --timeout-ms 900000 --json'
            )
        else:
            lines.append(
                '"$ORCA_BIN" orchestration check --wait --types worker_done --timeout-ms 900000 --json'
            )
        lines.append("")
    for gate in project["spec"].get("gates") or []:
        question = str(gate["question"]).replace('"', '\\"')
        options = json.dumps(gate["options"])
        lines.append(f"# HumanGate: {gate['id']} (orchestration)")
        lines.append(
            f'"$ORCA_BIN" orchestration gate-create --task "$RUN_ID" --question "{question}" --options \'{options}\' --json'
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
    if agent.get("worktree"):
        tree = (
            f"Isolated Orca worktree: `{agent['worktree']}`. "
            f"Create it with orca-cli (`worktree create --name {agent['worktree']}`). "
            "Never raw `git worktree`."
        )
    else:
        tree = "Lead / shared session. Do not create a worktree."
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
    binding = agent.get("skills") or skills_for(agent)
    primary = binding["primary"]
    required = ", ".join(binding["required"])
    why = binding["why"]
    knowledge = ""
    if graph.knowledge_bind:
        knowledge = "\n" + prompt_block(graph.knowledge_bind, str(agent.get("role") or "")) + "\n"
    return f"""---
name: {agent['name']}
host: {agent['host']}
role: {agent['role']}
ager_id: {agent['ager_id']}
skills_primary: {primary}
---

# {agent['name']}

{agent['instructions']}

{SKILL_PREAMBLE}

Primary skill: **{primary}**. Required: {required}.
{why}

{tree}
{judges}
{remote}

When your contracted files are written, report with `orchestration send --type worker_done`. Escalate with `orchestration ask` rather than inventing a side channel.

InputSchema: `{agent['input_schema']}`
OutputSchema: `{agent['output_schema']}`
LoopPolicy check order: {order}
Stop if max_turns={agent['budget']['max_turns']} or timeout_ms={agent['budget']['timeout_ms']}.

Write only the contracted files. Do not invent agents.
{knowledge}"""


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
        "ORCA_SKILLS.md": orca_skills_doc(),
        "scripts/run-feature.sh": run_script(project),
        "agents/Orca-Coordinator/SYSTEM.md": coordinator_prompt(project),
        "skills/orca-cli/SKILL.md": load_stub("orca-cli"),
        "skills/orchestration/SKILL.md": load_stub("orchestration"),
        "docs/planning/.gitkeep": "",
        "artifacts/critiques/.gitkeep": "",
        "artifacts/judgments/.gitkeep": "",
        "artifacts/implementations/.gitkeep": "",
    }
    if graph.knowledge_bind:
        files["knowledge-bind.yaml"] = f"# Generated by orca-ager@{PLUGIN_VERSION}\n{to_yaml(bind_spec(graph.knowledge_bind))}\n"
        files["SECOND_BRAIN.md"] = protocol_md(graph.knowledge_bind)
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
