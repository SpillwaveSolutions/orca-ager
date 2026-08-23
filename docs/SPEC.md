# Orca AGER Translator Specification

**Plugin name:** `orca-ager`  
**Spec version:** `0.2.0`  
**Date:** 2026-08-23  
**Status:** Draft for implementation  
**Authors:** Spillwave Solutions / Grok team (Rick Hightower request)  
**Depends on:** `okf-agent-graph` (AGER ≥ 0.3.0), `okf-graph-eng`, Orca ADE (stablyai/orca)

---

## 1. Purpose

This specification defines a bidirectional translator plugin that converts portable **AGER** (OKF Agent Graph Engineering Runtime) multi-agent graphs into executable **Orca** (Agent Development Environment) orchestration configurations, and (optionally) reverse-engineers Orca runs back into AGER concepts.

Orca is the open-source ADE from Stably AI that runs any CLI coding agent (Claude Code, Codex, Grok Build, Cursor, OpenCode, etc.) in isolated git worktrees, with parallel fan-out, side-by-side comparison, mobile companion, and agent-driven CLI control.

The translator enables the exact multi-model workflow described by the user:

1. Claude drafts a plan  
2. Grok Build + Codex review the plan in parallel  
3. Claude Code refines the plan and saves it under `docs/planning/<feature>-<date>.md`  
4. Three implementers (Claude, Grok, Codex) each work in their own git worktree  
5. Three judges critique the other implementations  
6. Grok Mediator selects a winner and has it steal the best ideas from the other two  
7. Final Spec Reviewer checks the result against the original plan  
8. PR is created and the winner is merged to main  

The translator produces named, human-readable Orca agents (so remote-control panes are not anonymous clutter) and optional remote-control disable or rename rules.

---

## 2. Design Principles

Aligned with AGER v0.3.0:

1. **Config, not framework** — AGER remains the source of truth; Orca is one runtime adapter among many (alongside LangGraph, CrewAI, Google ADK, Claude Agent SDK, etc.).
2. **Contracts first** — Every mapped AgentNode carries explicit InputSchema / OutputSchema (JSON Schema) that become Orca task contracts and file hand-off conventions.
3. **Loop engineering** — AGER LoopControl / LoopPolicy map to Orca task budgets, max-turns, deadlines, and no-progress guards.
4. **Salient KV** — ScratchPad and shared artifacts become the plan markdown, critique files, and worktree-local state that all agents can read.
5. **Ops under uncertainty** — FailurePolicy, RetryPolicy, and HumanGate become Orca approval gates, mobile notifications, and merge gates.
6. **Named agents** — Every generated Orca agent receives a stable, human-readable name (e.g. `Claude-Plan-Drafter`, `Grok-Mediator`) so the Orca UI and Claude Code remote-control list remain intelligible.
7. **Worktree isolation** — Parallel topology (FanOut / ParallelGroup) always maps to real git worktrees.

---

## 3. Core Mapping Table

| AGER Concept              | Orca Construct                                      | Notes |
|---------------------------|-----------------------------------------------------|-------|
| AgentGraph / AgentGraphModule | Orca Project / Task Group / Run                  | Top-level orchestration unit |
| OrchestratorAgent         | Lead Orca session or orchestrator worktree          | Plans, spawns, re-plans |
| WorkerAgent               | Orca agent session in isolated git worktree         | Named (Claude-Implementer, etc.) |
| JudgeAgent                | Dedicated judge worktree or post-run review agent   | Writes critique markdown |
| SynthesizerAgent          | Mediator / idea-steal step                          | Picks winner + merges good ideas |
| RouterAgent               | Conditional ControlEdge → Orca stage routing        | |
| GuardrailAgent            | Pre/post schema validation + ToolRule               | |
| HumanGate                 | Orca approval / mobile notification + merge gate    | |
| FanOut / ParallelGroup    | Parallel worktrees fan-out                          | One worktree per parallel agent |
| FanIn                     | Comparison / judgment stage                         | |
| LoopControl / LoopPolicy  | Task budget, max_turns, deadline, no_progress       | |
| ScratchPad                | Shared plan.md + critique files + artifacts dir      | |
| Tool + ToolRule           | **orca-cli** skill (worktree, terminal, handoff) | Prefer over raw `git worktree` |
| Run / Trigger             | **orchestration** skill: Run / Task / worker-start | Named `--name <Host>-<Role>` |
| Rubric / Judgment         | Judge critique files + final score                  | |
| Peer skills               | orca-cli + orchestration (stablyai/orca)            | Load live guides before commands |
| Coordinator loop          | Orca-Coordinator                                    | Drives the DAG; does not implement |

### Named Role Conventions (required)

The translator **must** emit human-readable names of the form:

```
<ModelOrHost>-<Role>
```

Examples used in the reference workflow:

- `Claude-Plan-Drafter`
- `Grok-Plan-Reviewer`
- `Codex-Plan-Reviewer`
- `Claude-Plan-Refiner`
- `Claude-Implementer`
- `Grok-Implementer`
- `Codex-Implementer`
- `Claude-Judge`
- `Grok-Judge`
- `Codex-Judge`
- `Grok-Mediator`
- `Final-Spec-Reviewer`

These names appear in the Orca UI, terminal titles, and (if remote control is left enabled) in Claude Code’s remote-control list so the user can instantly identify which agent is which.

Optional configuration:

```yaml
orca:
  remote_control: disable | rename   # default: rename
  name_prefix: ""                    # optional global prefix
```

---

## 4. Plugin Architecture

Follow the established Spillwave AGER translator pattern (see `google-adk-ager`, `langchain-deep-agents-ager`, `claude-agent-sdk-ager`, `crewai-ager`).

```
orca-ager/
├── .claude-plugin/          # Claude Code packaging
├── .codex-plugin/
├── .grok-plugin/
├── .cursor-plugin/
├── commands/                # Thin slash-command wrappers
│   ├── orca-init.md
│   ├── orca-compile.md
│   ├── orca-validate.md
│   └── orca-emit.md
├── skills/
│   └── ager-to-orca/
│       └── SKILL.md         # Main skill: author → emit → validate
├── scripts/
│   ├── emit.py              # Deterministic AGER → Orca generator
│   ├── validate.py          # Structural + semantic checks
│   └── reverse.py           # Optional AGKC-style reverse capture
├── scaffold/                # Canonical starter Orca project template
├── sample-orca/             # Worked example of the multi-model feature flow
├── docs/
│   ├── SPEC.md              # This document
│   ├── MAPPING.md
│   └── HOSTS.md
└── tests/
```

### Host Packaging

Installable via:

```bash
# Claude Code
claude plugin marketplace add SpillwaveSolutions/orca-ager
claude plugin install orca-ager@orca-ager-marketplace

# Codex / Grok Build (analogous marketplace add)
```

Slash commands:

- `/orca-init` — scaffold a new Orca-targeted AGER bundle
- `/orca-compile` or `/ager-to-orca` — emit Orca config + prompts + orchestration scripts from an existing AGER graph
- `/orca-validate` — validate the emitted artifacts

---

## 5. Generation Process

1. **Load** AGER bundle (OKF Markdown + YAML frontmatter).
2. **Validate** against AGER 0.3.0 contracts (reuse `ager-validate.py` + extra Orca rules).
3. **Topological sort** of AgentNodes, ParallelGroups, and ControlEdges.
4. **Emit**:
   - `orca-project.yaml` (or equivalent Orca task definition)
   - Per-agent prompt / system instruction files under `agents/<Name>/`
   - Worktree orchestration script (`scripts/run-feature.sh` or Orca CLI sequence)
   - Stage hand-off contracts (which files each stage reads/writes)
   - Optional `remote-control.json` rename map
5. **Validate** emitted artifacts (names unique, worktree paths non-overlapping, schemas present).
6. **Write** a short `COMPILE.md` report showing the mapping table used.

The primary deterministic engine lives in `scripts/emit.py` (Python, standard library + minimal deps) so it can be called from any host or CI.

---

## 6. Reference Workflow Encoding

The user’s exact multi-agent feature development flow is encoded as a reusable AGER graph module and emitted as an Orca project template.

### Stages (high level)

```text
Trigger: "start new feature: <description>"
    │
    ▼
[Claude-Plan-Drafter]  ──► draft-plan.md
    │
    ├─► [Grok-Plan-Reviewer]  ──► critique-grok.md
    └─► [Codex-Plan-Reviewer] ──► critique-codex.md
    │
    ▼
[Claude-Plan-Refiner]  ──► docs/planning/<feature>-<YYYY-MM-DD>.md   (final plan)
    │
    ├─► [Claude-Implementer]   (worktree: wt-claude)
    ├─► [Grok-Implementer]     (worktree: wt-grok)
    └─► [Codex-Implementer]    (worktree: wt-codex)
    │
    ├─► [Claude-Judge]  (reviews the other two)
    ├─► [Grok-Judge]
    └─► [Codex-Judge]
    │
    ▼
[Grok-Mediator]  ──► selects winner + instructs winner to steal good ideas
    │
    ▼
[Final-Spec-Reviewer]  ──► final code review against plan
    │
    ▼
PR creation + merge to main (HumanGate optional)
```

All intermediate artifacts (plans, critiques, judgments) are written into a shared `artifacts/` or second-brain OKF location following the user’s existing isolation rules (pull main to read, branch + PR to write).

---

## 7. Second-Brain / OKF Integration

Because many of the user’s projects already use an OKF second-brain repo:

- Agents that need to record tickets, decisions, or SLDC notes must follow the second-brain write protocol (own worktree → branch → PR → merge).
- The translator can optionally emit a `KnowledgeBind` / `RetrievalBinding` that points agents at the second-brain root.
- Critiques, judgments, and final decisions become `DecisionRecord` or `TicketLink` concepts when the second-brain bridge is enabled.

---

## 8. Acceptance Criteria for v0.2

- [x] `scripts/emit.py` can take a valid AGER 0.3.0 bundle and produce a runnable Orca project skeleton.
- [x] All generated agents receive stable, human-readable names of the form `<Host>-<Role>`.
- [x] Parallel stages create distinct git worktrees via **orca-cli** (never raw `git worktree`).
- [x] Plan, critique, and judgment files follow the user’s `docs/planning/` and artifact conventions.
- [x] Optional remote-control rename or disable is emitted.
- [x] A sample AGER graph for the multi-model feature workflow is included and successfully compiles.
- [x] Host packaging works for Claude Code, Codex, and Grok Build.
- [x] Validation fails loudly on missing schemas, name collisions, or overlapping worktree paths.
- [x] Every SYSTEM.md instructs the agent to load `orca-cli` and `orchestration` live guides.
- [x] The stage DAG is emitted as orchestration primitives plus an Orca-Coordinator.
- [x] Plugin vendors orca-cli and orchestration discovery stubs.

---

## 9. Implementation Notes & Next Steps

1. Start from the `google-adk-ager` or `claude-agent-sdk-ager` skeleton (host packaging, skills, emit.py pattern).
2. Define the Orca target schema (YAML or JSON) based on current Orca CLI / project conventions (worktrees, agent CLI command, task metadata).
3. Implement the named-role mapping and remote-control policy first — this is the user’s most immediate pain point.
4. Encode the reference multi-model workflow as the primary sample.
5. Add reverse engineering later (`ager-scan` style detection of Orca runs → draft AGER).

Once this specification is accepted, the implementation can proceed in a separate Grok Build / Claude Code session as requested.

---

## 10. References

- AGER Specification v0.3.0 — SpillwaveSolutions/okf-agent-graph
- Existing translators: google-adk-ager, langchain-deep-agents-ager, crewai-ager, claude-agent-sdk-ager, claude-managed-agents-ager
- Orca ADE — https://github.com/stablyai/orca · https://www.onorca.dev/
- User workflow description (this conversation, 2026-08-23)

---

*End of specification.*
