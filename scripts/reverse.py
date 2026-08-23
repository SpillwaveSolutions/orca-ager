#!/usr/bin/env python3
"""Optional AGKC-style reverse capture: Orca project YAML → draft AGER graph."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ir import AgerGraph, Agent, HumanGate, LoopPolicy, SchemaRef, Stage
from layout import to_yaml, write

TYPE_FROM_ROLE = {
    "Plan-Drafter": "OrchestratorAgent",
    "Plan-Refiner": "OrchestratorAgent",
    "Plan-Reviewer": "JudgeAgent",
    "Implementer": "WorkerAgent",
    "Judge": "JudgeAgent",
    "Mediator": "SynthesizerAgent",
    "Spec-Reviewer": "GuardrailAgent",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def reverse_project(raw: dict[str, Any]) -> AgerGraph:
    spec = _as_dict(raw.get("spec"))
    meta = _as_dict(raw.get("metadata"))
    agents: list[Agent] = []
    for item in _as_list(spec.get("agents")):
        row = _as_dict(item)
        role = str(row.get("role") or "Worker")
        ager_id = str(row.get("ager_id") or row.get("name") or "agent")
        agents.append(
            Agent(
                id=ager_id,
                type=TYPE_FROM_ROLE.get(role, "WorkerAgent"),
                host=str(row.get("host") or "claude"),
                role=role,
                title=str(row.get("name") or role),
                description=f"Reverse-captured from Orca project as {row.get('name')}.",
                instructions="",
                input_schema=SchemaRef(str(row.get("input_schema") or "schemas/input.schema.json"), {"type": "object"}),
                output_schema=SchemaRef(str(row.get("output_schema") or "schemas/output.schema.json"), {"type": "object"}),
                stage=str(row.get("stage") or "default"),
                parallel_group=str(row["parallel_group"]) if row.get("parallel_group") else None,
                worktree=str(row["worktree"]) if row.get("worktree") else None,
                reads=[str(x) for x in _as_list(row.get("reads"))],
                writes=[str(x) for x in _as_list(row.get("writes"))],
                judge_targets=[str(x) for x in _as_list(row.get("judge_targets"))],
                record_key=ager_id,
            )
        )
    stages = [
        Stage(
            id=str(row.get("id")),
            title=str(row.get("title") or row.get("id")),
            parallel=bool(row.get("parallel")),
            isolated_worktrees=bool(row.get("isolated_worktrees")),
            agents=[str(x) for x in _as_list(row.get("agents"))],
        )
        for item in _as_list(spec.get("stages"))
        for row in [_as_dict(item)]
    ]
    gate_raw = _as_list(spec.get("gates"))
    gate = None
    if gate_raw:
        g = _as_dict(gate_raw[0])
        gate = HumanGate(
            id=str(g.get("id") or "merge-gate"),
            title="PR and merge",
            after=str(g.get("after") or (agents[-1].id if agents else "")),
            question=str(g.get("question") or ""),
            options=[str(x) for x in _as_list(g.get("options"))] or ["merge", "hold"],
            action=str(g.get("action") or "pr_and_merge"),
        )
    return AgerGraph(
        id=str(meta.get("ager_id") or meta.get("name") or "reversed-graph"),
        title=str(meta.get("title") or "Reversed Orca project"),
        description="Draft AGER graph reverse-engineered from an Orca project. Promote before treating as normative.",
        ager_version=str(meta.get("ager_version") or "0.3.0"),
        entry=agents[0].id if agents else "",
        objective=str(spec.get("objective") or ""),
        agents=agents,
        stages=stages,
        parallel_groups=[],
        loop=LoopPolicy(8, 0.0, 600_000, ["goal", "deadline", "price_budget", "max_turns", "no_progress"]),
        remote_control="rename",
        gate=gate,
    )


def graph_to_compact(graph: AgerGraph) -> dict[str, Any]:
    return {
        "ager_version": graph.ager_version,
        "id": graph.id,
        "title": graph.title,
        "description": graph.description,
        "entry": graph.entry,
        "objective": graph.objective,
        "orca": {"remote_control": graph.remote_control, "name_prefix": graph.name_prefix},
        "loop": {
            "max_turns": graph.loop.max_turns,
            "price_budget_usd": graph.loop.price_budget_usd,
            "deadline_ms": graph.loop.deadline_ms,
            "check_order": graph.loop.check_order,
            "on_goal": graph.loop.on_goal,
            "on_exhaust": graph.loop.on_exhaust,
        },
        "stages": [
            {
                "id": s.id,
                "title": s.title,
                "parallel": s.parallel,
                "isolated_worktrees": s.isolated_worktrees,
                "agents": s.agents,
            }
            for s in graph.stages
        ],
        "parallel_groups": [
            {"id": g.id, "title": g.title, "members": g.members, "isolated_worktrees": g.isolated_worktrees}
            for g in graph.parallel_groups
        ],
        "gate": None
        if not graph.gate
        else {
            "id": graph.gate.id,
            "title": graph.gate.title,
            "after": graph.gate.after,
            "question": graph.gate.question,
            "options": graph.gate.options,
            "action": graph.gate.action,
        },
        "agents": [
            {
                "id": a.id,
                "type": a.type,
                "host": a.host,
                "role": a.role,
                "title": a.title,
                "description": a.description,
                "stage": a.stage,
                "worktree": a.worktree,
                "reads": a.reads,
                "writes": a.writes,
                "judge_targets": a.judge_targets,
            }
            for a in graph.agents
        ],
    }


def load_orca_project(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except Exception:
        # Fallback: only JSON-compatible orca-project dumps.
        raise SystemExit("reverse.py needs PyYAML to parse orca-project.yaml, or pass a JSON dump")


def main() -> None:
    parser = argparse.ArgumentParser(prog="orca-ager-reverse")
    parser.add_argument("--project", type=Path, required=True, help="orca-project.yaml or JSON")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    graph = reverse_project(load_orca_project(args.project))
    dest = write(args.out, "reversed-ager.yaml", f"# Draft AGER — reverse-captured, not normative\n{to_yaml(graph_to_compact(graph))}\n")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
