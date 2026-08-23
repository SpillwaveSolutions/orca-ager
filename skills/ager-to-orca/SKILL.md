---
name: ager-to-orca
description: Translate a validated AGER/OKF AgentGraph into Orca ADE orchestration with named worktree agents, parallel fan-out, and remote-control rename or disable.
---

# AGER → Orca ADE

This plugin **compiles**. Authoring is `okf-agent-graph`.

Orca is the ADE from Stably AI (`stablyai/orca`). It has no native AGER YAML; this translator emits `orca-project.yaml`, named `worker-start --name`, isolated git worktrees, and a remote-control rename map.

## Mapping

| AGER | Orca |
| --- | --- |
| AgentGraph | Orca Project / Run |
| OrchestratorAgent | Named lead session (no isolated worktree) |
| WorkerAgent | Named agent in isolated git worktree |
| JudgeAgent | Dedicated judge worktree; writes critique markdown |
| SynthesizerAgent | Mediator / idea-steal step |
| GuardrailAgent | Final spec review against the plan |
| HumanGate | `orca orchestration gate-create` |
| FanOut / ParallelGroup | Parallel worktrees, one per agent |
| LoopPolicy | Task budget, max_turns, deadline, no_progress |
| ScratchPad | `docs/planning/` + `artifacts/` |

Named roles are required: `<Host>-<Role>` (Claude-Plan-Drafter, Grok-Mediator). Remote-control policy is `rename` (default) or `disable`.

## Steps

1. Locate the AGER bundle. Validate with `ager-validate` if present.
2. Run the deterministic emitter. Do not freehand the tree.

```bash
python3 scripts/emit.py --bundle <AGER_ROOT> --out <OUT>
python3 scripts/emit.py --bundle <AGER_ROOT> --out <OUT> --remote-control disable
python3 scripts/emit.py --bundle <AGER_ROOT> --out <OUT> --name-prefix Fleet
python3 scripts/validate.py --bundle <AGER_ROOT>
```

3. Report written paths. Confirm every agent matches `<Host>-<Role>` and parallel worktrees do not overlap.
4. Never claim production-ready without tests. Hosts do not meter USD; document the budget and stop.

## References

- `references/mapping.md`
- [docs/SPEC.md](../../docs/SPEC.md)
- https://github.com/stablyai/orca
- https://www.onorca.dev/
