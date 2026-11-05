# Repository source map

This is a navigation aid, not a second specification or a snapshot of implementation status. Verify current code, tests, and plans in the checkout before making claims.

| Need | Start here | Follow with |
| --- | --- | --- |
| Repository rules and collaboration | `AGENTS.md` | The relevant project plan and local README |
| Project overview and intended scope | `README.md` | `CONTEXT.md` for vocabulary; `SYSTEM-DESIGN.md` for architecture and behavior |
| Backend scoring or turn lifecycle | `docs/BACKEND-SCORING-PLAN.md` | `SYSTEM-DESIGN.md`, then the current backend code/tests if present |
| Frontend scope, design, or canvas behavior | `docs/FRONTEND-BASE-SCOPE.md` | `docs/FRONTEND-IMPLEMENTATION-PLAN.md`, `docs/FRONTEND-VALIDATION.md`, `apps/web/README.md`, and the relevant `apps/web/` code/tests |
| Visual tokens and assets | `docs/design-system/DESIGN.md` | `docs/design-system/DESIGN-HANDOFF.md`, `docs/design-system/tokens.css`, `docs/design-system/tokens.json`, and referenced assets |
| Guesser evaluation or inference research | `models/guesser/evaluation/README.md` | `models/guesser/evaluation/pyproject.toml`, `models/guesser/evaluation/src/`, `models/guesser/evaluation/tests/`, and `models/guesser/evaluation/notebooks/` as relevant |

## Evidence and precedence

- `AGENTS.md` supplies repository-specific working constraints; follow it before general conventions.
- `README.md`, `CONTEXT.md`, and `SYSTEM-DESIGN.md` describe project intent, terminology, and system contracts. Task-specific plans refine their area.
- Current source code and tests show what is implemented in this checkout. A plan describes intended behavior; it does not prove implementation.
- Validation reports record checks at a particular time/environment. Re-run the relevant checks before claiming they pass now.
- If project documents conflict, use the latest explicit user decision where known. If that does not resolve the conflict, report it and ask rather than inferring from document dates or diagrams.
