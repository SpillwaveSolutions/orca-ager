# orca-ager

AGER → **Orca ADE** translator plugin.

Author graphs with [`okf-agent-graph`](https://github.com/SpillwaveSolutions/okf-agent-graph). This plugin compiles.

Orca is the open-source ADE from [Stably AI](https://www.onorca.dev/) that runs CLI coding agents (Claude Code, Codex, Grok Build, Cursor, …) in isolated git worktrees. AGER stays the portable config; Orca is one runtime adapter among LangGraph, CrewAI, Google ADK, and Claude Agent SDK.

## What it emits

- `orca-project.yaml` — named agents, stages, LoopPolicy, HumanGate
- `agents/<Host>-<Role>/SYSTEM.md` + `contract.json`
- `scripts/run-feature.sh` — `worktree create` + `worker-start --name`
- `remote-control.json` — rename map or disable list
- `COMPILE.md` + `handoffs.md`

Named roles are required: `Claude-Plan-Drafter`, `Grok-Mediator`, `Final-Spec-Reviewer`. Parallel implementers get `wt-claude` / `wt-grok` / `wt-codex`.

A host gets a manifest, never a fork. See [docs/HOSTS.md](docs/HOSTS.md). Mapping: [docs/MAPPING.md](docs/MAPPING.md). Spec: [docs/SPEC.md](docs/SPEC.md).

## Install

```bash
claude plugin marketplace add SpillwaveSolutions/orca-ager
claude plugin install orca-ager@orca-ager-marketplace

codex plugin marketplace add SpillwaveSolutions/orca-ager
```

Cursor: `/plugin install orca-ager` — [docs/CURSOR.md](docs/CURSOR.md).

## Use

```
/orca-init
/orca-compile
/orca-validate
```

```bash
python3 scripts/emit.py --bundle sample-ager --out ./generated
python3 scripts/emit.py --bundle sample-ager --out ./generated --remote-control disable
python3 scripts/emit.py --bundle sample-ager --out ./generated --name-prefix Fleet
python3 scripts/validate.py --bundle sample-ager
python3 -m unittest tests/test_plugin.py
```

## Sample workflow

The bundled graph is the 12-agent multi-model feature flow:

1. Claude-Plan-Drafter
2. Grok-Plan-Reviewer + Codex-Plan-Reviewer (parallel)
3. Claude-Plan-Refiner → `docs/planning/<feature>-<date>.md`
4. Claude-Implementer / Grok-Implementer / Codex-Implementer (isolated worktrees)
5. Claude-Judge / Grok-Judge / Codex-Judge (cross-critique, never self)
6. Grok-Mediator (winner + steal)
7. Final-Spec-Reviewer
8. HumanGate PR merge

## License

MIT
