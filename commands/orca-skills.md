---
name: orca-skills
description: Install and load the official Orca peer skills (orca-cli, orchestration) required by compiled AGER fleets.
---

# /orca-skills

Compiled orca-ager fleets run inside Orca ADE. Install **orca-cli**, **orchestration**, and **ager-to-orca** from this plugin. The Orca binary still serves the live command guide.

## Install

```bash
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill ager-to-orca --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orca-cli --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orchestration --global
```

```bash
orca skills install --skill orca-cli --skill orchestration
# optional: --agent claude-code,codex,grok
# optional: --local
```

This plugin also vendors the stubs at `skills/orca-cli/SKILL.md` and `skills/orchestration/SKILL.md`.

## Load before any Orca command

```bash
orca skills get orca-cli
orca skills get orchestration --full
```

Prefer `--json` for agent-driven calls. Confirm the app with `orca status --json` (`orca open --json` if needed).

Linux outside an Orca-managed terminal: use `orca-ide`, never bare `orca` (GNOME screen reader).

## When to use which

- **orca-cli** — named worktrees, terminals, full handoffs, snapshots. Prefer over raw `git worktree`.
- **orchestration** — Runs, Tasks, `worker-start --name <Host>-<Role>`, `check --wait --types worker_done,escalation`, `gate-create`, coordinator loops. This is plan → review → implement → judge → mediate.

Every generated `SYSTEM.md` already instructs the agent to load both skills. `/orca-compile` emits `ORCA_SKILLS.md` and `agents/Orca-Coordinator/SYSTEM.md`.
