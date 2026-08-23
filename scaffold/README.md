# Orca-targeted AGER scaffold

Copy `sample-ager/` and rename the graph id. Keep named roles `<Host>-<Role>`.

```bash
cp -R sample-ager my-feature
python3 scripts/emit.py --bundle my-feature --out ./generated
```

Rules:

1. Every AgentNode has InputSchema and OutputSchema.
2. Parallel isolated stages each get a unique worktree.
3. `orca.remote_control` is `rename` or `disable`.
4. Do not invent agents that are not in the graph.
