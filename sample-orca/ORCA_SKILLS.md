# Orca skills for this compiled project

AGER compiled this fleet to run **inside Orca ADE**. Two peer skills from [stablyai/orca](https://github.com/stablyai/orca) are required. They are discovery stubs — load the live, version-matched guide from the running binary before any command.

## Install

```bash
npx skills add https://github.com/stablyai/orca --skill orca-cli --global
npx skills add https://github.com/stablyai/orca --skill orchestration --global
```

```bash
orca skills install --skill orca-cli --skill orchestration
# optional: --agent claude-code,codex,grok
# optional: --local   (this project only)
```

## Load (every session, before mutating state)

```bash
orca skills get orca-cli
orca skills get orchestration --full
```

Use `--json` when an agent needs deterministic output.

## When to use which

| Skill | Use for |
| --- | --- |
| **orca-cli** | Named worktrees (`wt-claude`, `wt-grok`, `wt-codex`), terminals, full handoffs, snapshots, embedded browser. Prefer over raw `git worktree`. |
| **orchestration** | `run-create`, `task-create`, `worker-start --name <Host>-<Role>`, `check --wait --types worker_done,escalation,question`, `gate-create`, coordinator loops. This is the plan → review → implement → judge → mediate DAG. |

The generated coordinator (`agents/Orca-Coordinator/SYSTEM.md`) drives the DAG with the orchestration skill. Isolated implementers and judges use orca-cli for their worktrees and send `worker_done` on the orchestration bus.

## Verify

```bash
orca status --json
orca skills list
orca skills get orca-cli
```

Linux outside an Orca-managed terminal: use `orca-ide`, never bare `orca` (GNOME screen reader).
