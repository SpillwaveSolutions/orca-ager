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
