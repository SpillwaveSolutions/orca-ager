#!/usr/bin/env python3
"""Structural + semantic checks for AGER graphs and emitted Orca projects."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ir import AgerGraph, load_bundle

NAMED_ROLE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*(-[A-Z][A-Za-z0-9]*)+$")


@dataclass
class Issue:
    level: str
    code: str
    message: str
    path: str | None = None


@dataclass
class Result:
    ok: bool
    errors: list[Issue]
    warnings: list[Issue]


def _result(issues: list[Issue]) -> Result:
    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    return Result(ok=not errors, errors=errors, warnings=warnings)


def validate_graph(graph: AgerGraph) -> Result:
    issues: list[Issue] = []
    if not graph.id:
        issues.append(Issue("error", "graph.id", "Graph id is required."))
    if not graph.entry:
        issues.append(Issue("error", "graph.entry", "Graph entry agent is required."))
    ids: set[str] = set()
    for agent in graph.agents:
        if agent.id in ids:
            issues.append(Issue("error", "agent.duplicate", f"Duplicate agent id '{agent.id}'.", agent.id))
        ids.add(agent.id)
        if not agent.input_schema or not agent.input_schema.schema:
            issues.append(Issue("error", "schema.input", f"Missing InputSchema on '{agent.id}'.", agent.id))
        if not agent.output_schema or not agent.output_schema.schema:
            issues.append(Issue("error", "schema.output", f"Missing OutputSchema on '{agent.id}'.", agent.id))
    if graph.entry and graph.entry not in ids:
        issues.append(Issue("error", "graph.entry.missing", f"Entry '{graph.entry}' is not in the agent list."))
    for group in graph.parallel_groups:
        if len(group.members) < 2:
            issues.append(
                Issue("error", "parallel.size", f"ParallelGroup '{group.id}' must have at least two members.", group.id)
            )
        for member in group.members:
            if member not in ids:
                issues.append(
                    Issue(
                        "error",
                        "parallel.member",
                        f"ParallelGroup '{group.id}' references unknown agent '{member}'.",
                        group.id,
                    )
                )
    return _result(issues)


def validate_project(project: dict[str, Any]) -> Result:
    issues: list[Issue] = []
    spec = project.get("spec") or {}
    agents = spec.get("agents") or []
    stages = spec.get("stages") or []
    names: set[str] = set()
    worktrees: dict[str, str] = {}
    by_name: dict[str, dict[str, Any]] = {}
    for agent in agents:
        name = str(agent.get("name") or "")
        if name in names:
            issues.append(Issue("error", "name.collision", f"Orca agent name '{name}' is not unique.", name))
        names.add(name)
        by_name[name] = agent
        if not NAMED_ROLE_RE.match(name):
            issues.append(
                Issue(
                    "error",
                    "name.pattern",
                    f"Agent '{name}' must match <Host>-<Role> (e.g. Claude-Plan-Drafter).",
                    name,
                )
            )
        if not agent.get("input_schema"):
            issues.append(Issue("error", "schema.input", f"Missing input schema for '{name}'.", name))
        if not agent.get("output_schema"):
            issues.append(Issue("error", "schema.output", f"Missing output schema for '{name}'.", name))
        tree = agent.get("worktree")
        if tree:
            owner = worktrees.get(tree)
            if owner and owner != name:
                issues.append(
                    Issue(
                        "error",
                        "worktree.overlap",
                        f"Worktree '{tree}' is claimed by both '{owner}' and '{name}'.",
                        tree,
                    )
                )
            worktrees[tree] = name
    for stage in stages:
        if stage.get("parallel") and stage.get("isolated_worktrees"):
            trees = []
            for name in stage.get("agents") or []:
                agent = by_name.get(name)
                trees.append((agent or {}).get("worktree"))
            present = [t for t in trees if t]
            if len(set(present)) != len(present):
                issues.append(
                    Issue(
                        "error",
                        "worktree.parallel",
                        f"Parallel stage '{stage.get('id')}' has overlapping worktrees.",
                        str(stage.get("id")),
                    )
                )
            if len(present) != len(stage.get("agents") or []):
                issues.append(
                    Issue(
                        "error",
                        "worktree.required",
                        f"Parallel isolated stage '{stage.get('id')}' requires a worktree on every agent.",
                        str(stage.get("id")),
                    )
                )
    policy = ((spec.get("remote_control") or {}).get("policy")) or "rename"
    if policy not in {"rename", "disable"}:
        issues.append(Issue("error", "remote_control", "remote_control must be 'rename' or 'disable'."))
    return _result(issues)


def report(result: Result) -> str:
    lines = []
    for issue in result.errors:
        loc = f" ({issue.path})" if issue.path else ""
        lines.append(f"ERROR {issue.code}{loc}: {issue.message}")
    for issue in result.warnings:
        loc = f" ({issue.path})" if issue.path else ""
        lines.append(f"WARN  {issue.code}{loc}: {issue.message}")
    if result.ok:
        lines.append("ok")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="orca-ager-validate")
    parser.add_argument("--bundle", type=Path)
    args = parser.parse_args()
    graph = load_bundle(args.bundle)
    result = validate_graph(graph)
    print(report(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
