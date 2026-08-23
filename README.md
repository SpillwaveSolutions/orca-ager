# orca-ager

AGER → **Orca ADE** translator plugin.

Author graphs with [`okf-agent-graph`](https://github.com/SpillwaveSolutions/okf-agent-graph). This plugin compiles.

Orca is the open-source ADE from [Stably AI](https://www.onorca.dev/) that runs CLI coding agents (Claude Code, Codex, Grok Build, Cursor, …) in isolated git worktrees. AGER stays the portable config; Orca is one runtime adapter among LangGraph, CrewAI, Google ADK, and Claude Agent SDK.

Compiled fleets **use the official Orca skills** — `orca-cli` for named worktrees / terminals / handoffs, `orchestration` for the plan → review → implement → judge → mediate DAG.

## What it emits

- `orca-project.yaml` — named agents, stages, LoopPolicy, HumanGate, peer skills, coordinator
- `agents/<Host>-<Role>/SYSTEM.md` + `contract.json` — every prompt loads orca-cli + orchestration
- `agents/Orca-Coordinator/SYSTEM.md` — orchestration coordinator loop
- `scripts/run-feature.sh` — resolves `orca-ide` on Linux, loads live skill guides, then `worktree create` + `worker-start --name`
- `skills/orca-cli/SKILL.md` + `skills/orchestration/SKILL.md` — discovery stubs (live guide from the binary)
- `ORCA_SKILLS.md` — install + load
- `remote-control.json` — rename map or disable list
- `COMPILE.md` + `handoffs.md`

Named roles are required: `Claude-Plan-Drafter`, `Grok-Mediator`, `Final-Spec-Reviewer`. Parallel implementers get `wt-claude` / `wt-grok` / `wt-codex` via **orca-cli**, never raw `git worktree`.

A host gets a manifest, never a fork. See [docs/HOSTS.md](docs/HOSTS.md). Mapping: [docs/MAPPING.md](docs/MAPPING.md). Spec: [docs/SPEC.md](docs/SPEC.md).

## Install

```bash
claude plugin marketplace add SpillwaveSolutions/orca-ager
claude plugin install orca-ager@orca-ager-marketplace

codex plugin marketplace add SpillwaveSolutions/orca-ager
```

Cursor: `/plugin install orca-ager` — [docs/CURSOR.md](docs/CURSOR.md).

Peer Orca skills (required at runtime):

```bash
npx skills add https://github.com/stablyai/orca --skill orca-cli --global
npx skills add https://github.com/stablyai/orca --skill orchestration --global
orca skills get orca-cli
orca skills get orchestration --full
```

## Use

```
/orca-init
/orca-skills
/orca-compile
/orca-validate
/orca-reverse
```

```bash
python3 scripts/emit.py --bundle sample-ager --out ./generated
python3 scripts/emit.py --bundle sample-ager --out ./generated --remote-control disable
python3 scripts/emit.py --bundle sample-ager --out ./generated --name-prefix Fleet
python3 scripts/validate.py --bundle sample-ager
python3 scripts/reverse.py --project sample-orca/orca-project.yaml --out ./reversed
python3 -m unittest tests/test_plugin.py
```

## Sample workflow

The bundled graph is the 12-agent multi-model feature flow, driven by **Orca-Coordinator**:

1. Claude-Plan-Drafter
2. Grok-Plan-Reviewer + Codex-Plan-Reviewer (parallel)
3. Claude-Plan-Refiner → `docs/planning/<feature>-<date>.md`
4. Claude-Implementer / Grok-Implementer / Codex-Implementer (isolated orca-cli worktrees)
5. Claude-Judge / Grok-Judge / Codex-Judge (cross-critique, never self)
6. Grok-Mediator (winner + steal)
7. Final-Spec-Reviewer
8. HumanGate PR merge (`orchestration gate-create`)

## License

MIT
