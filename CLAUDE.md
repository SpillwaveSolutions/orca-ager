# CLAUDE.md — orca-ager

Translator. Compiles a validated AGER/OKF AgentGraph into **Orca ADE**.

```bash
python3 scripts/emit.py --bundle sample-ager --out ./generated
python3 scripts/validate.py --bundle sample-ager
```

Do not author a new AGER graph (that is `okf-agent-graph`). Do not invent agents.
Honor LoopPolicy check order: goal → deadline → price → max_turns → no_progress.
Named roles are required. Remote-control policy is `rename` (default) or `disable`.

<!-- worklog:policy:start -->
## WikiTicket SDD (worklog)

This plugin tracks implementation with [WikiTicket SDD](https://github.com/SpillwaveSolutions/wiki_ticket_sdd).

- Install the `worklog` plugin from `SpillwaveSolutions/wiki_ticket_sdd`.
- Config lives in `.work/config.yml`. Event log is `.work/todo.jsonl`.
- Every plan MUST end by running `worklog plan-capture`.
- Work discovered mid-flight: `worklog add --unplanned --discovered-during <item>` BEFORE doing the work.
- Never hand-edit `.work/*.jsonl` (use `worklog`) or `docs/roadmap.md` (generated).
- After changing work items, run `worklog roadmap-render` and commit the log and roadmap together.
<!-- worklog:policy:end -->
