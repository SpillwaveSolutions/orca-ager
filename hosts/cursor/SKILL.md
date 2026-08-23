---
name: cursor-orca-ager
description: Bind a Cursor agent to orca-ager. Compile AGER graphs into Orca ADE. Do not author graphs.
---

# Cursor / orca-ager

Follow `docs/CURSOR.md` and `docs/HOSTS.md`.

1. Identity: `cursor/orca-ager`.
2. Local Cursor may `/plugin install orca-ager`.
3. Compile with `python3 scripts/emit.py --bundle <AGER> --out <OUT>`.
4. Never invent agents. Never write a new AGER graph (that is `okf-agent-graph`).
