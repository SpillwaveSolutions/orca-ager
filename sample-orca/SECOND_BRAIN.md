# Second-brain / OKF bind

This project is bound to `second-brain/`.

## Write protocol

1. **Read** — pull `main`. Never write on `main`.
2. **Write** — own worktree → branch `okf/<record>` → PR → merge.
3. Critiques, judgments, and the winner decision are **DecisionRecords**.
4. The refined plan and HumanGate merge are **TicketLinks**.

## Record map

| Kind | From run artifacts | Into second-brain |
| --- | --- | --- |
| `DecisionRecord` | `artifacts/judgments/` | `second-brain/decisions/` |
| `DecisionRecord` | `artifacts/critiques/` | `second-brain/decisions/critiques/` |
| `TicketLink` | `docs/planning/` | `second-brain/tickets/` |
