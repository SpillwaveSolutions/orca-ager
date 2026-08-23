# AGER → Orca mapping

| AGER Concept | Orca Construct | Notes |
| --- | --- | --- |
| AgentGraph / AgentGraphModule | Orca Project / Task Group / Run | `orca-project.yaml` |
| OrchestratorAgent | Lead Orca session | Named, no isolated worktree. Primary skill: orchestration. |
| WorkerAgent | Agent session in isolated git worktree | `Claude-Implementer` in `wt-claude` via **orca-cli** |
| JudgeAgent | Judge worktree or post-run reviewer | Writes critique markdown; never scores self |
| SynthesizerAgent | Mediator / idea-steal | Picks winner + merge of good ideas |
| RouterAgent | Conditional ControlEdge → stage routing | Task DAG |
| GuardrailAgent | Schema validation + ToolRule | `Final-Spec-Reviewer` |
| HumanGate | Approval / mobile notification + merge gate | `orchestration gate-create` |
| FanOut / ParallelGroup | Parallel named worktrees | One worktree per parallel agent (orca-cli, not raw git) |
| FanIn | Comparison / judgment stage | Judges read sibling trees |
| LoopControl / LoopPolicy | Task budget, max_turns, deadline, no_progress | Check order: goal → deadline → price → max_turns → no_progress |
| ScratchPad | Shared plan.md + critiques + artifacts | `docs/planning/<feature>-<date>.md` |
| Tool + ToolRule | **orca-cli** skill | worktree create, terminal send/wait, full handoff, snapshot |
| Run / Trigger | **orchestration** skill | `run-create` + `task-create` + `worker-start --name` |
| Rubric / Judgment | Judge critique files + final score | `artifacts/judgments/judge-<host>.md` |
| Named roles | `<Host>-<Role>` titles | Remote-control list stays intelligible |
| Peer skills | orca-cli + orchestration via orca-ager plugin | Install: `npx skills add https://github.com/SpillwaveSolutions/orca-ager --skill orca-cli` |
| Coordinator loop | Orca-Coordinator | Drives the DAG; does not implement the feature |
| KnowledgeBind / RetrievalBinding | second-brain/ + DecisionRecord / TicketLink | Pull main to read. Own worktree → branch → PR to write. |
