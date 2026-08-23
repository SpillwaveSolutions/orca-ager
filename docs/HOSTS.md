# Host matrix

`orca-ager` is one plugin, five install surfaces. Skills live once under `skills/`.

| Host | Manifest | Install |
| --- | --- | --- |
| Agent Plugins 1.0 | `plugin.json` | any host that reads agent-plugins.org |
| Claude Code | `.claude-plugin/plugin.json` + `marketplace.json` | `claude plugin marketplace add SpillwaveSolutions/orca-ager` |
| Grok Build | `.grok-plugin/marketplace.json` (Claude layout is zero-config) | drop into workspace / Claude marketplace |
| Codex | `.codex-plugin/plugin.json` | `codex plugin marketplace add SpillwaveSolutions/orca-ager` |
| Cursor | `.cursor-plugin/plugin.json` + `.cursor/rules/` | `/plugin install orca-ager` |

Command on Claude/Grok: `/orca-compile`
Command on Codex: `$orca-compile`

Depends on `okf-agent-graph` for author/validate. This plugin only compiles.
Orca ADE is the runtime: https://github.com/stablyai/orca · https://www.onorca.dev/

Peer skills from the orca-ager plugin (required at runtime):

```bash
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill ager-to-orca --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orca-cli --global
npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orchestration --global
orca skills get orca-cli
orca skills get orchestration --full
```

Worktrees and handoffs use **orca-cli**. The plan → review → implement → judge → mediate DAG uses **orchestration**. Never raw `git worktree`.
