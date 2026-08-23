# sample-orca

Generated output of `python3 scripts/emit.py --bundle sample-ager --out sample-orca`.

Do not edit by hand. Re-emit after graph changes.

Entry: **Claude-Plan-Drafter**. Coordinator: **Orca-Coordinator**. Remote-control: **rename**. Isolated implementer worktrees: `wt-claude`, `wt-grok`, `wt-codex` via orca-cli.

Peer skills: `orca-cli` + `orchestration`. See `ORCA_SKILLS.md`.

```bash
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill ager-to-orca --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orca-cli --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orchestration --global
bash scripts/run-feature.sh "start new feature: <description>"
```
