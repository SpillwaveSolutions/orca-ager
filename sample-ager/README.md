# sample-ager — multi-model feature workflow

Canonical 12-agent graph used by `orca-ager`.

| Stage | Agents | Isolation |
| --- | --- | --- |
| plan-draft | Claude-Plan-Drafter | lead session |
| plan-review | Grok-Plan-Reviewer, Codex-Plan-Reviewer | parallel, shared |
| plan-refine | Claude-Plan-Refiner | lead session |
| implement | Claude / Grok / Codex Implementer | isolated worktrees |
| judge | Claude / Grok / Codex Judge | isolated judge worktrees |
| mediate | Grok-Mediator | lead session |
| spec-review | Final-Spec-Reviewer | lead session |
| merge | HumanGate | approval |

The Python IR in `scripts/ir.py` is the source of truth for emit. Markdown here is the human-readable module.
