---
name: orca-compile
description: Compile an AGER AgentGraph into an Orca ADE project (named agents, worktrees, orca-cli + orchestration skills, run script).
---

Follow the **ager-to-orca** skill completely. Confirm orca-cli and orchestration are installed (`/orca-skills`) and load `orca skills get orca-cli` plus `orca skills get orchestration --full` before guessing any Orca flag. Run `scripts/emit.py`. Report written paths. Do not freehand the tree. Every SYSTEM.md must tell the agent to load those two skills. Worktrees via orca-cli, DAG via orchestration.
