# Orca skills for this compiled project

AGER compiled this fleet to run **inside Orca ADE**. Install the skills from the **orca-ager plugin** ([SpillwaveSolutions/orca-ager](https://github.com/SpillwaveSolutions/orca-ager)). Discovery stubs ship in the plugin; the running Orca binary still serves the live command guide.

## Install (from the plugin)

```bash
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill ager-to-orca --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orca-cli --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orchestration --global
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
| **ager-to-orca** | Compile / validate / reverse AGER graphs (this plugin). |
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
