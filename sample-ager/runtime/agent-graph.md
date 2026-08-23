---
ager_version: "0.3.0"
id: multi-model-feature
title: Multi-model feature workflow
description: Claude drafts, Grok and Codex review in parallel, three implementers ship in isolated worktrees, three judges score the others, Grok mediates, a spec reviewer gates the PR.
entry: claude-plan-drafter
objective: "start new feature: <description>"
orca:
  remote_control: rename
  name_prefix: ""
---

# Multi-model feature workflow

AGER 0.3.0 module. Authoritative compile input is `scripts/ir.py` `load_sample()`. Compact YAML lives in `graph.yaml`.

Trigger: `start new feature: <description>`

```text
[Claude-Plan-Drafter]  ──► draft-plan.md
    ├─► [Grok-Plan-Reviewer]  ──► critique-grok.md
    └─► [Codex-Plan-Reviewer] ──► critique-codex.md
[Claude-Plan-Refiner]  ──► docs/planning/<feature>-<YYYY-MM-DD>.md
    ├─► [Claude-Implementer]   (wt-claude)
    ├─► [Grok-Implementer]     (wt-grok)
    └─► [Codex-Implementer]    (wt-codex)
    ├─► [Claude-Judge]  (reviews the other two)
    ├─► [Grok-Judge]
    └─► [Codex-Judge]
[Grok-Mediator]  ──► winner + steal
[Final-Spec-Reviewer] ──► spec-review.md
HumanGate PR merge
```

LoopPolicy check order: goal → deadline → price_budget → max_turns → no_progress.

Compile:

```bash
python3 scripts/emit.py --bundle sample-ager --out ./generated
```
