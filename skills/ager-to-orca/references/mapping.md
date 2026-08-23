# AGER → Orca mapping

| AGER Concept | Orca Construct | Notes |
| --- | --- | --- |
| AgentGraph / AgentGraphModule | Orca Project / Task Group / Run | `orca-project.yaml` |
| OrchestratorAgent | Lead Orca session | Named, no isolated worktree |
| WorkerAgent | Agent session in isolated git worktree | `Claude-Implementer` in `wt-claude` |
| JudgeAgent | Judge worktree or post-run reviewer | Writes critique markdown; never scores self |
| SynthesizerAgent | Mediator / idea-steal | Picks winner + merge of good ideas |
| RouterAgent | Conditional ControlEdge → stage routing | Task DAG |
| GuardrailAgent | Schema validation + ToolRule | `Final-Spec-Reviewer` |
| HumanGate | Approval / mobile notification + merge gate | `gate-create` |
| FanOut / ParallelGroup | Parallel worktrees | One worktree per parallel agent |
| FanIn | Comparison / judgment stage | Judges read sibling trees |
| LoopControl / LoopPolicy | Task budget, max_turns, deadline, no_progress | Check order: goal → deadline → price → max_turns → no_progress |
| ScratchPad | Shared plan.md + critiques + artifacts | `docs/planning/<feature>-<date>.md` |
| Tool + ToolRule | Agent CLI + Orca CLI | worktree create, snapshot, terminal send |
| Run / Trigger | Orca Run / Task | `start new feature: <description>` |
| Rubric / Judgment | Judge critique files + final score | `artifacts/judgments/judge-<host>.md` |
| Named roles | `<Host>-<Role>` titles | Remote-control list stays intelligible |
