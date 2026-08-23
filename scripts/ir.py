#!/usr/bin/env python3
"""AGER IR for the Orca translator. Sample is the multi-model feature graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


HOST_LABEL = {
    "claude": "Claude",
    "grok": "Grok",
    "codex": "Codex",
    "cursor": "Cursor",
    "gemini": "Gemini",
    "opencode": "OpenCode",
    "droid": "Droid",
    "final": "Final",
    "human": "Human",
}
HOST_CLI = {
    "claude": "claude",
    "grok": "grok",
    "codex": "codex",
    "cursor": "cursor",
    "gemini": "gemini",
    "opencode": "opencode",
    "droid": "droid",
    "final": "claude",
    "human": "human",
}


@dataclass
class SchemaRef:
    path: str
    schema: dict[str, Any]


@dataclass
class Agent:
    id: str
    type: str
    host: str
    role: str
    title: str
    description: str
    instructions: str
    tools: list[str] = field(default_factory=list)
    input_schema: SchemaRef = field(default_factory=lambda: SchemaRef("schemas/in.json", {"type": "object"}))
    output_schema: SchemaRef = field(default_factory=lambda: SchemaRef("schemas/out.json", {"type": "object"}))
    stage: str = "default"
    parallel_group: str | None = None
    worktree: str | None = None
    reads: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)
    judge_targets: list[str] = field(default_factory=list)
    record_key: str = ""
    record_mode: str = "append"
    max_turns: int = 8
    timeout_ms: int = 180000
    ephemeral: bool = False
    links: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Stage:
    id: str
    title: str
    parallel: bool
    isolated_worktrees: bool
    agents: list[str]


@dataclass
class ParallelGroup:
    id: str
    title: str
    members: list[str]
    isolated_worktrees: bool


@dataclass
class LoopPolicy:
    max_turns: int
    price_budget_usd: float
    deadline_ms: int
    check_order: list[str]
    on_goal: str = "return"
    on_exhaust: str = "return_best"


@dataclass
class HumanGate:
    id: str
    title: str
    after: str
    question: str
    options: list[str]
    action: str


@dataclass
class AgerGraph:
    id: str
    title: str
    description: str
    ager_version: str
    entry: str
    objective: str
    agents: list[Agent]
    stages: list[Stage]
    parallel_groups: list[ParallelGroup]
    loop: LoopPolicy
    remote_control: str = "rename"
    name_prefix: str = ""
    gate: HumanGate | None = None
    knowledge_bind: str | None = None


def _schema(name: str, properties: dict[str, Any], required: list[str]) -> SchemaRef:
    return SchemaRef(
        f"schemas/{name}.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": name,
            "type": "object",
            "additionalProperties": False,
            "required": required,
            "properties": properties,
        },
    )


BRIEF = _schema("feature-brief", {"description": {"type": "string"}, "constraints": {"type": "array", "items": {"type": "string"}}}, ["description"])
DRAFT = _schema("draft-plan", {"title": {"type": "string"}, "summary": {"type": "string"}, "steps": {"type": "array", "items": {"type": "string"}}}, ["title", "summary", "steps"])
CRITIQUE = _schema("plan-critique", {"author": {"type": "string"}, "findings": {"type": "array", "items": {"type": "string"}}, "score": {"type": "number"}}, ["author", "findings", "score"])
FINAL = _schema("final-plan", {"feature": {"type": "string"}, "date": {"type": "string"}, "path": {"type": "string"}, "acceptance": {"type": "array", "items": {"type": "string"}}}, ["feature", "date", "path", "acceptance"])
IMPL = _schema("implementation", {"worktree": {"type": "string"}, "summary": {"type": "string"}, "files": {"type": "array", "items": {"type": "string"}}}, ["worktree", "summary", "files"])
JUDGMENT = _schema("judgment", {"judge": {"type": "string"}, "subjects": {"type": "array", "items": {"type": "string"}}, "scores": {"type": "object"}, "pass": {"type": "boolean"}}, ["judge", "subjects", "scores", "pass"])
DECISION = _schema("mediator-decision", {"winner": {"type": "string"}, "rationale": {"type": "string"}}, ["winner", "rationale"])
SPEC = _schema("spec-review", {"matchesPlan": {"type": "boolean"}, "readyToMerge": {"type": "boolean"}}, ["matchesPlan", "readyToMerge"])


def _agent(**kwargs: Any) -> Agent:
    return Agent(**kwargs)


def load_sample() -> AgerGraph:
    return AgerGraph(
        id="multi-model-feature",
        title="Multi-model feature workflow",
        description="Claude drafts, Grok and Codex review in parallel, three implementers ship in isolated worktrees, three judges score the others, Grok mediates, a spec reviewer gates the PR.",
        ager_version="0.3.0",
        entry="claude-plan-drafter",
        objective="start new feature: <description>",
        remote_control="rename",
        loop=LoopPolicy(12, 25.0, 14_400_000, ["goal", "deadline", "price_budget", "max_turns", "no_progress"]),
        stages=[
            Stage("plan-draft", "Draft plan", False, False, ["claude-plan-drafter"]),
            Stage("plan-review", "Parallel plan review", True, False, ["grok-plan-reviewer", "codex-plan-reviewer"]),
            Stage("plan-refine", "Refine plan", False, False, ["claude-plan-refiner"]),
            Stage("implement", "Parallel implementers", True, True, ["claude-implementer", "grok-implementer", "codex-implementer"]),
            Stage("judge", "Cross-critique", True, True, ["claude-judge", "grok-judge", "codex-judge"]),
            Stage("mediate", "Mediate and steal", False, False, ["grok-mediator"]),
            Stage("spec-review", "Final spec review", False, False, ["final-spec-reviewer"]),
        ],
        parallel_groups=[
            ParallelGroup("plan-review", "Plan reviewers", ["grok-plan-reviewer", "codex-plan-reviewer"], False),
            ParallelGroup("implement", "Implementers", ["claude-implementer", "grok-implementer", "codex-implementer"], True),
            ParallelGroup("judge", "Judges", ["claude-judge", "grok-judge", "codex-judge"], True),
        ],
        gate=HumanGate(
            "merge-gate",
            "PR and merge",
            "final-spec-reviewer",
            "Create the PR from the winning worktree and merge to main?",
            ["merge", "hold"],
            "pr_and_merge",
        ),
        knowledge_bind="second-brain/",
        agents=[
            _agent(
                id="claude-plan-drafter",
                type="OrchestratorAgent",
                host="claude",
                role="Plan-Drafter",
                title="Claude-Plan-Drafter",
                description="Drafts the feature plan from the trigger description.",
                instructions="You are Claude-Plan-Drafter. Read the feature trigger. Write a structured draft plan covering intent, constraints, files likely to change, test plan, and risks. Do not implement. Write artifacts/draft-plan.md and stop.",
                tools=["Read", "Write"],
                input_schema=BRIEF,
                output_schema=DRAFT,
                stage="plan-draft",
                worktree=None,
                writes=["artifacts/draft-plan.md"],
                record_key="draft_plan",
                record_mode="set",
            ),
            _agent(
                id="grok-plan-reviewer",
                type="JudgeAgent",
                host="grok",
                role="Plan-Reviewer",
                title="Grok-Plan-Reviewer",
                description="Critiques the draft plan in parallel with Codex.",
                instructions="You are Grok-Plan-Reviewer. Read artifacts/draft-plan.md. Stress-test feasibility, missing edge cases, and over-scoping. Write artifacts/critiques/critique-grok.md. Do not rewrite the plan.",
                tools=["Read", "Write"],
                input_schema=DRAFT,
                output_schema=CRITIQUE,
                stage="plan-review",
                parallel_group="plan-review",
                reads=["artifacts/draft-plan.md"],
                writes=["artifacts/critiques/critique-grok.md"],
                judge_targets=["claude-plan-drafter"],
                record_key="plan_critiques",
            ),
            _agent(
                id="codex-plan-reviewer",
                type="JudgeAgent",
                host="codex",
                role="Plan-Reviewer",
                title="Codex-Plan-Reviewer",
                description="Critiques the draft plan in parallel with Grok.",
                instructions="You are Codex-Plan-Reviewer. Read artifacts/draft-plan.md. Focus on implementation sequencing, testability, and API contracts. Write artifacts/critiques/critique-codex.md.",
                tools=["Read", "Write"],
                input_schema=DRAFT,
                output_schema=CRITIQUE,
                stage="plan-review",
                parallel_group="plan-review",
                reads=["artifacts/draft-plan.md"],
                writes=["artifacts/critiques/critique-codex.md"],
                judge_targets=["claude-plan-drafter"],
                record_key="plan_critiques",
            ),
            _agent(
                id="claude-plan-refiner",
                type="OrchestratorAgent",
                host="claude",
                role="Plan-Refiner",
                title="Claude-Plan-Refiner",
                description="Merges critiques into the durable planning document.",
                instructions="You are Claude-Plan-Refiner. Read the draft plan and both critiques. Produce the final plan at docs/planning/<feature>-<YYYY-MM-DD>.md. Include acceptance criteria.",
                tools=["Read", "Write"],
                input_schema=CRITIQUE,
                output_schema=FINAL,
                stage="plan-refine",
                reads=["artifacts/draft-plan.md", "artifacts/critiques/critique-grok.md", "artifacts/critiques/critique-codex.md"],
                writes=["docs/planning/<feature>-<YYYY-MM-DD>.md"],
                record_key="final_plan",
                record_mode="set",
            ),
            _agent(
                id="claude-implementer",
                type="WorkerAgent",
                host="claude",
                role="Implementer",
                title="Claude-Implementer",
                description="Implements the plan in worktree wt-claude.",
                instructions="You are Claude-Implementer. Work only in git worktree wt-claude. Implement the final plan. Do not read other implementer worktrees.",
                tools=["Read", "Write", "Bash", "Edit"],
                input_schema=FINAL,
                output_schema=IMPL,
                stage="implement",
                parallel_group="implement",
                worktree="wt-claude",
                reads=["docs/planning/<feature>-<YYYY-MM-DD>.md"],
                writes=["artifacts/implementations/claude.md"],
                record_key="implementations",
                max_turns=24,
                timeout_ms=900000,
                ephemeral=True,
            ),
            _agent(
                id="grok-implementer",
                type="WorkerAgent",
                host="grok",
                role="Implementer",
                title="Grok-Implementer",
                description="Implements the plan in worktree wt-grok.",
                instructions="You are Grok-Implementer. Work only in git worktree wt-grok. Implement the final plan.",
                tools=["Read", "Write", "Bash", "Edit"],
                input_schema=FINAL,
                output_schema=IMPL,
                stage="implement",
                parallel_group="implement",
                worktree="wt-grok",
                reads=["docs/planning/<feature>-<YYYY-MM-DD>.md"],
                writes=["artifacts/implementations/grok.md"],
                record_key="implementations",
                max_turns=24,
                timeout_ms=900000,
                ephemeral=True,
            ),
            _agent(
                id="codex-implementer",
                type="WorkerAgent",
                host="codex",
                role="Implementer",
                title="Codex-Implementer",
                description="Implements the plan in worktree wt-codex.",
                instructions="You are Codex-Implementer. Work only in git worktree wt-codex. Implement the final plan.",
                tools=["Read", "Write", "Bash", "Edit"],
                input_schema=FINAL,
                output_schema=IMPL,
                stage="implement",
                parallel_group="implement",
                worktree="wt-codex",
                reads=["docs/planning/<feature>-<YYYY-MM-DD>.md"],
                writes=["artifacts/implementations/codex.md"],
                record_key="implementations",
                max_turns=24,
                timeout_ms=900000,
                ephemeral=True,
            ),
            _agent(
                id="claude-judge",
                type="JudgeAgent",
                host="claude",
                role="Judge",
                title="Claude-Judge",
                description="Scores Grok and Codex implementations; never its own.",
                instructions="You are Claude-Judge. Review wt-grok and wt-codex against the final plan. Do not review wt-claude. Write artifacts/judgments/judge-claude.md.",
                tools=["Read", "Write", "Bash"],
                input_schema=IMPL,
                output_schema=JUDGMENT,
                stage="judge",
                parallel_group="judge",
                worktree="wt-judge-claude",
                reads=["docs/planning/<feature>-<YYYY-MM-DD>.md"],
                writes=["artifacts/judgments/judge-claude.md"],
                judge_targets=["grok-implementer", "codex-implementer"],
                record_key="judgments",
                max_turns=10,
                timeout_ms=300000,
            ),
            _agent(
                id="grok-judge",
                type="JudgeAgent",
                host="grok",
                role="Judge",
                title="Grok-Judge",
                description="Scores Claude and Codex implementations; never its own.",
                instructions="You are Grok-Judge. Review wt-claude and wt-codex against the final plan. Write artifacts/judgments/judge-grok.md.",
                tools=["Read", "Write", "Bash"],
                input_schema=IMPL,
                output_schema=JUDGMENT,
                stage="judge",
                parallel_group="judge",
                worktree="wt-judge-grok",
                reads=["docs/planning/<feature>-<YYYY-MM-DD>.md"],
                writes=["artifacts/judgments/judge-grok.md"],
                judge_targets=["claude-implementer", "codex-implementer"],
                record_key="judgments",
                max_turns=10,
                timeout_ms=300000,
            ),
            _agent(
                id="codex-judge",
                type="JudgeAgent",
                host="codex",
                role="Judge",
                title="Codex-Judge",
                description="Scores Claude and Grok implementations; never its own.",
                instructions="You are Codex-Judge. Review wt-claude and wt-grok against the final plan. Write artifacts/judgments/judge-codex.md.",
                tools=["Read", "Write", "Bash"],
                input_schema=IMPL,
                output_schema=JUDGMENT,
                stage="judge",
                parallel_group="judge",
                worktree="wt-judge-codex",
                reads=["docs/planning/<feature>-<YYYY-MM-DD>.md"],
                writes=["artifacts/judgments/judge-codex.md"],
                judge_targets=["claude-implementer", "grok-implementer"],
                record_key="judgments",
                max_turns=10,
                timeout_ms=300000,
            ),
            _agent(
                id="grok-mediator",
                type="SynthesizerAgent",
                host="grok",
                role="Mediator",
                title="Grok-Mediator",
                description="Selects the winner and instructs it to steal the best ideas.",
                instructions="You are Grok-Mediator. Read all three judgments. Select a winning implementer. List ideas to steal from the other two. Write artifacts/decision.md.",
                tools=["Read", "Write"],
                input_schema=JUDGMENT,
                output_schema=DECISION,
                stage="mediate",
                reads=["artifacts/judgments/judge-claude.md", "artifacts/judgments/judge-grok.md", "artifacts/judgments/judge-codex.md"],
                writes=["artifacts/decision.md"],
                record_key="decision",
                record_mode="set",
            ),
            _agent(
                id="final-spec-reviewer",
                type="GuardrailAgent",
                host="final",
                role="Spec-Reviewer",
                title="Final-Spec-Reviewer",
                description="Checks the winning tree against the original plan.",
                instructions="You are Final-Spec-Reviewer. Diff the winning worktree against the final plan. Write artifacts/spec-review.md. Block merge if the plan is not met.",
                tools=["Read", "Write", "Bash"],
                input_schema=DECISION,
                output_schema=SPEC,
                stage="spec-review",
                reads=["docs/planning/<feature>-<YYYY-MM-DD>.md", "artifacts/decision.md"],
                writes=["artifacts/spec-review.md"],
                record_key="spec_review",
                record_mode="set",
            ),
        ],
    )


def _frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    meta: dict[str, Any] = {}
    for line in text[3:end].splitlines():
        if ":" not in line or line.startswith(" ") or line.startswith("-"):
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def load_bundle(path: Path | None) -> AgerGraph:
    graph = load_sample()
    if path is None:
        return graph
    root = Path(path)
    graph_md = root / "runtime" / "agent-graph.md"
    if graph_md.exists():
        meta = _frontmatter(graph_md.read_text(encoding="utf-8"))
        if meta.get("title"):
            graph.title = meta["title"]
        if meta.get("description"):
            graph.description = meta["description"]
        if meta.get("ager_version"):
            graph.ager_version = meta["ager_version"]
    return graph
