# WORKLOG

v0.2.0 — official Orca skills + reverse capture.

- Vendored `orca-cli` + `orchestration` discovery stubs from stablyai/orca
- Every SYSTEM.md loads `orca skills get orca-cli` and `orca skills get orchestration --full`
- Isolated worktrees via orca-cli (never raw git worktree)
- Stage DAG via orchestration primitives + Orca-Coordinator
- `scripts/run-feature.sh` resolves `orca-ide` on Linux, installs/loads skills, then runs the DAG
- `/orca-skills` command
- Reverse capture: `scripts/reverse.py` + `/orca-reverse` drafts AGER from `orca-project.yaml`
- Studio Skills + Reverse tabs

v0.1.0 — initial AGER → Orca ADE translator.

- Named roles `<Host>-<Role>`
- Isolated worktrees for parallel implementers and judges
- Remote-control rename (default) or disable
- Sample 12-agent multi-model feature graph
- Host packaging: Agent Plugins 1.0, Claude Code, Grok Build, Codex, Cursor
