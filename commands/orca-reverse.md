---
name: orca-reverse
description: Reverse-capture an Orca project (orca-project.yaml) into a draft AGER graph. Promote before treating as normative.
---

# /orca-reverse

AGER remains the source of truth. This command drafts a graph from a compiled Orca project so you can recover a lost AGER bundle.

```bash
python3 scripts/reverse.py --project <orca-project.yaml> --out ./reversed
```

The draft:

- Maps `<Host>-<Role>` names back to AGER ids
- Recovers stages, isolated worktrees, LoopPolicy, HumanGate, remote-control policy
- Drops **Orca-Coordinator** (runtime only; re-emitted on the next compile)
- Is **not normative** until you review and promote it

Do not invent agents while reversing. If `ager-validate` is available, validate the draft before compiling it again.
