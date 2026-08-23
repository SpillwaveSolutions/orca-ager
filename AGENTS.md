# AGENTS.md — orca-ager

Translator. Compiles AGER → **Orca ADE**.

- `/orca-init` `/orca-compile` `/orca-validate` `/orca-emit` `/ager-to-orca` `/orca-skills` `/orca-reverse`
- `python3 scripts/emit.py --bundle path/to/ager --out ./generated`
- `--remote-control rename|disable`  `--name-prefix <Fleet>`

Every generated agent is named `<Host>-<Role>` (Claude-Plan-Drafter, Grok-Mediator).
Parallel isolated stages get distinct git worktrees via **orca-cli**, never raw `git worktree`. Fail on overlap or missing schemas.

Peer skills (required): `orca-cli` and `orchestration` from stablyai/orca. Load live guides (`orca skills get orca-cli`, `orca skills get orchestration --full`) before mutating ADE state. The coordinator loop is orchestration; worktrees/handoffs are orca-cli.

Hosts: Agent Plugins 1.0, Claude Code, Grok Build, Codex, Cursor.

<!-- worklog:policy:start -->
## WikiTicket SDD (worklog)

This plugin tracks implementation with [WikiTicket SDD](https://github.com/SpillwaveSolutions/wiki_ticket_sdd).

- Install the `worklog` plugin from `SpillwaveSolutions/wiki_ticket_sdd` (Claude Code, Grok Build, Codex, Cursor).
- Config lives in `.work/config.yml`. Event log is `.work/todo.jsonl`.
- Every plan MUST end by running `worklog plan-capture`.
- Work discovered mid-flight: `worklog add --unplanned --discovered-during <item>` BEFORE doing the work.
- Never hand-edit `.work/*.jsonl` (use `worklog`) or `docs/roadmap.md` (generated).
- After changing work items, run `worklog roadmap-render` and commit the log and roadmap together.
- CLI: `worklog` on PATH, or `python3 <wiki_ticket_sdd>/bin/worklog`.
<!-- worklog:policy:end -->
