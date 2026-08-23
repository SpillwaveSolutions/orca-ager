---
name: ager-to-orca
description: Translate a validated AGER/OKF AgentGraph into Orca ADE orchestration with named worktree agents, parallel fan-out, remote-control rename or disable, and official orca-cli + orchestration skills.
---

# AGER → Orca ADE

This plugin **compiles**. Authoring is `okf-agent-graph`.

Orca is the ADE from Stably AI (`stablyai/orca`). It has no native AGER YAML; this translator emits `orca-project.yaml`, named `worker-start --name`, isolated git worktrees, a remote-control rename map, and a coordinator that drives the DAG with official Orca skills.

## Peer skills (required)

Compiled fleets run inside Orca. Before emitting or running, install and load:

```bash
npx skills add https://github.com/stablyai/orca --skill orca-cli --global
npx skills add https://github.com/stablyai/orca --skill orchestration --global
orca skills get orca-cli
orca skills get orchestration --full
```

| Skill | Translator use |
| --- | --- |
| **orca-cli** | Named worktrees, terminals, full handoffs. Prefer over raw `git worktree`. |
| **orchestration** | Run / Task / worker DAG, `worker_done` waits, decision gates, coordinator loop. Maps onto plan → review → implement → judge → mediate. |

The plugin vendors the discovery stubs under `skills/orca-cli` and `skills/orchestration`. They are not the command reference — the running binary is.

## Mapping

| AGER | Orca |
| --- | --- |
| AgentGraph | Orca Project / Run (`orchestration run-create`) |
| OrchestratorAgent | Named lead session (no isolated worktree) |
| WorkerAgent | Named agent in isolated git worktree via **orca-cli** |
| JudgeAgent | Dedicated judge worktree; writes critique markdown |
| SynthesizerAgent | Mediator / idea-steal step on the orchestration DAG |
| GuardrailAgent | Final spec review against the plan |
| HumanGate | `orchestration gate-create` |
| FanOut / ParallelGroup | Parallel named worktrees, one per agent |
| LoopPolicy | Task budget, max_turns, deadline, no_progress |
| ScratchPad | `docs/planning/` + `artifacts/` |

Named roles are required: `<Host>-<Role>` (Claude-Plan-Drafter, Grok-Mediator). Remote-control policy is `rename` (default) or `disable`.

## Steps

1. Locate the AGER bundle. Validate with `ager-validate` if present.
2. Confirm orca-cli and orchestration are installed (see above). Load the live guides. Do not guess Orca flags.
3. Run the deterministic emitter. Do not freehand the tree.

```bash
python3 scripts/emit.py --bundle <AGER_ROOT> --out <OUT>
python3 scripts/emit.py --bundle <AGER_ROOT> --out <OUT> --remote-control disable
python3 scripts/emit.py --bundle <AGER_ROOT> --out <OUT> --name-prefix Fleet
python3 scripts/validate.py --bundle <AGER_ROOT>
```

4. Report written paths. Confirm:
   - every agent matches `<Host>-<Role>`
   - parallel worktrees do not overlap
   - every `SYSTEM.md` instructs the agent to `orca skills get orca-cli` and `orca skills get orchestration --full`
   - `scripts/run-feature.sh` uses orca-cli worktrees (not raw git) and orchestration primitives
   - `agents/Orca-Coordinator/SYSTEM.md` is present
5. Never claim production-ready without tests. Hosts do not meter USD; document the budget and stop.

## References

- `references/mapping.md`
- [docs/SPEC.md](../../docs/SPEC.md)
- https://github.com/stablyai/orca
- https://www.onorca.dev/docs/cli/skills
