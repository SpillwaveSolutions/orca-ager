# Stage hand-off contracts

Plan files live under `docs/planning/`. Critiques and judgments live under `artifacts/`.

| Agent | Reads | Writes |
| --- | --- | --- |
| **Claude-Plan-Drafter** | — | artifacts/draft-plan.md |
| **Grok-Plan-Reviewer** | artifacts/draft-plan.md | artifacts/critiques/critique-grok.md |
| **Codex-Plan-Reviewer** | artifacts/draft-plan.md | artifacts/critiques/critique-codex.md |
| **Claude-Plan-Refiner** | artifacts/draft-plan.md, artifacts/critiques/critique-grok.md, artifacts/critiques/critique-codex.md | docs/planning/<feature>-<YYYY-MM-DD>.md |
| **Claude-Implementer** | docs/planning/<feature>-<YYYY-MM-DD>.md | artifacts/implementations/claude.md |
| **Grok-Implementer** | docs/planning/<feature>-<YYYY-MM-DD>.md | artifacts/implementations/grok.md |
| **Codex-Implementer** | docs/planning/<feature>-<YYYY-MM-DD>.md | artifacts/implementations/codex.md |
| **Claude-Judge** | docs/planning/<feature>-<YYYY-MM-DD>.md | artifacts/judgments/judge-claude.md |
| **Grok-Judge** | docs/planning/<feature>-<YYYY-MM-DD>.md | artifacts/judgments/judge-grok.md |
| **Codex-Judge** | docs/planning/<feature>-<YYYY-MM-DD>.md | artifacts/judgments/judge-codex.md |
| **Grok-Mediator** | artifacts/judgments/judge-claude.md, artifacts/judgments/judge-grok.md, artifacts/judgments/judge-codex.md | artifacts/decision.md |
| **Final-Spec-Reviewer** | docs/planning/<feature>-<YYYY-MM-DD>.md, artifacts/decision.md | artifacts/spec-review.md |
