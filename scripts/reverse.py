#!/usr/bin/env python3
"""AGKC-style reverse capture: Orca project YAML → draft AGER graph.

The draft is not normative. Promote after review. Coordinator is an Orca
runtime agent and is not written back into the AGER graph.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ir import AgerGraph, Agent, HumanGate, LoopPolicy, ParallelGroup, SchemaRef, Stage
from layout import parse_yaml, to_yaml, write

TYPE_FROM_ROLE = {
    "Plan-Drafter": "OrchestratorAgent",
    "Plan-Refiner": "OrchestratorAgent",
    "Plan-Reviewer": "JudgeAgent",
    "Implementer": "WorkerAgent",
    "Judge": "JudgeAgent",
    "Mediator": "SynthesizerAgent",
    "Spec-Reviewer": "GuardrailAgent",
    "Coordinator": "OrchestratorAgent",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_str(value: Any, fallback: str = "") -> str:
    return str(value) if value is not None and not isinstance(value, (dict, list)) else fallback


def _as_int(value: Any, fallback: int) -> int:
    if isinstance(value, bool) or value is None:
        return fallback
    if isinstance(value, (int, float)):
        return int(value)
    return fallback


def _as_float(value: Any, fallback: float) -> float:
    if isinstance(value, bool) or value is None:
        return fallback
    if isinstance(value, (int, float)):
        return float(value)
    return fallback


def reverse_project(raw: dict[str, Any]) -> AgerGraph:
    spec = _as_dict(raw.get("spec"))
    meta = _as_dict(raw.get("metadata"))
    agents: list[Agent] = []
    name_to_id: dict[str, str] = {}
    for item in _as_list(spec.get("agents")):
        row = _as_dict(item)
        name = _as_str(row.get("name"))
        role = _as_str(row.get("role") or "Worker")
        if role == "Coordinator" or name == "Orca-Coordinator":
            continue
        ager_id = _as_str(row.get("ager_id") or name or "agent")
        name_to_id[name] = ager_id
        name_to_id[ager_id] = ager_id
        budget = _as_dict(row.get("budget"))
        agent_type = _as_str(row.get("type")) or TYPE_FROM_ROLE.get(role, "WorkerAgent")
        agents.append(
            Agent(
                id=ager_id,
                type=agent_type,
                host=_as_str(row.get("host") or "claude"),
                role=role,
                title=name or role,
                description=_as_str(row.get("description") or f"Reverse-captured as {name}."),
                instructions=_as_str(row.get("instructions")),
                tools=[],
                input_schema=SchemaRef(_as_str(row.get("input_schema") or "schemas/input.schema.json"), {"type": "object"}),
                output_schema=SchemaRef(_as_str(row.get("output_schema") or "schemas/output.schema.json"), {"type": "object"}),
                stage=_as_str(row.get("stage") or "default"),
                parallel_group=_as_str(row["parallel_group"]) if row.get("parallel_group") else None,
                worktree=_as_str(row["worktree"]) if row.get("worktree") else None,
                reads=[_as_str(x) for x in _as_list(row.get("reads"))],
                writes=[_as_str(x) for x in _as_list(row.get("writes"))],
                judge_targets=[_as_str(x) for x in _as_list(row.get("judge_targets"))],
                record_key=ager_id,
                max_turns=_as_int(budget.get("max_turns"), 8),
                timeout_ms=_as_int(budget.get("timeout_ms"), 180_000),
            )
        )

    def resolve(name: str) -> str:
        return name_to_id.get(name, name)

    stages: list[Stage] = []
    groups: list[ParallelGroup] = []
    for item in _as_list(spec.get("stages")):
        row = _as_dict(item)
        members = [resolve(_as_str(x)) for x in _as_list(row.get("agents"))]
        isolated = bool(row.get("isolated_worktrees"))
        parallel = bool(row.get("parallel"))
        stage_id = _as_str(row.get("id"))
        title = _as_str(row.get("title") or stage_id)
        stages.append(Stage(stage_id, title, parallel, isolated, members))
        if parallel:
            groups.append(ParallelGroup(stage_id, title, members, isolated))

    gate_raw = _as_list(spec.get("gates"))
    gate = None
    if gate_raw:
        g = _as_dict(gate_raw[0])
        after = resolve(_as_str(g.get("after") or (agents[-1].id if agents else "")))
        gate = HumanGate(
            id=_as_str(g.get("id") or "merge-gate"),
            title=_as_str(g.get("title") or "PR and merge"),
            after=after,
            question=_as_str(g.get("question")),
            options=[_as_str(x) for x in _as_list(g.get("options"))] or ["merge", "hold"],
            action=_as_str(g.get("action") or "pr_and_merge"),
        )

    loop_raw = _as_dict(spec.get("loop"))
    order = [_as_str(x) for x in _as_list(loop_raw.get("check_order"))]
    loop = LoopPolicy(
        max_turns=_as_int(loop_raw.get("max_turns"), 8),
        price_budget_usd=_as_float(loop_raw.get("price_budget_usd"), 0.0),
        deadline_ms=_as_int(loop_raw.get("deadline_ms"), 600_000),
        check_order=order or ["goal", "deadline", "price_budget", "max_turns", "no_progress"],
        on_goal=_as_str(loop_raw.get("on_goal") or "return"),
        on_exhaust=_as_str(loop_raw.get("on_exhaust") or "return_best"),
    )
    remote = _as_dict(spec.get("remote_control"))
    policy = _as_str(remote.get("policy") or "rename")
    if policy not in {"rename", "disable"}:
        policy = "rename"
    return AgerGraph(
        id=_as_str(meta.get("ager_id") or meta.get("name") or "reversed-graph"),
        title=_as_str(meta.get("title") or "Reversed Orca project"),
        description="Draft AGER graph reverse-engineered from an Orca project. Promote before treating as normative.",
        ager_version=_as_str(meta.get("ager_version") or "0.3.0"),
        entry=agents[0].id if agents else "",
        objective=_as_str(spec.get("objective")),
        agents=agents,
        stages=stages,
        parallel_groups=groups,
        loop=loop,
        remote_control=policy,
        name_prefix=_as_str(remote.get("name_prefix")),
        gate=gate,
        knowledge_bind=_as_str(_as_dict(spec.get("knowledge_bind")).get("root")) or None,
    )


def graph_to_compact(graph: AgerGraph) -> dict[str, Any]:
    return {
        "ager_version": graph.ager_version,
        "id": graph.id,
        "title": graph.title,
        "description": graph.description,
        "entry": graph.entry,
        "objective": graph.objective,
        "knowledge_bind": graph.knowledge_bind,
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
                "instructions": a.instructions,
                "stage": a.stage,
                "parallel_group": a.parallel_group,
                "worktree": a.worktree,
                "reads": a.reads,
                "writes": a.writes,
                "judge_targets": a.judge_targets,
                "input_schema": a.input_schema.path,
                "output_schema": a.output_schema.path,
                "max_turns": a.max_turns,
                "timeout_ms": a.timeout_ms,
            }
            for a in graph.agents
        ],
    }


def load_orca_project(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    data = parse_yaml(text)
    if not isinstance(data, dict):
        raise SystemExit("orca-project.yaml did not parse as a mapping")
    return data


def reverse_summary(graph: AgerGraph) -> dict[str, Any]:
    return {
        "id": graph.id,
        "title": graph.title,
        "agents": len(graph.agents),
        "stages": [s.id for s in graph.stages],
        "worktrees": [a.worktree for a in graph.agents if a.worktree],
        "entry": graph.entry,
        "draft": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="orca-ager-reverse")
    parser.add_argument("--project", type=Path, required=True, help="orca-project.yaml or JSON")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    graph = reverse_project(load_orca_project(args.project))
    dest = write(
        args.out,
        "reversed-ager.yaml",
        "# Draft AGER — reverse-captured from Orca. Promote before treating as normative.\n"
        f"{to_yaml(graph_to_compact(graph))}\n",
    )
    print(f"wrote {dest}")
    print(json.dumps(reverse_summary(graph)))


if __name__ == "__main__":
    main()
