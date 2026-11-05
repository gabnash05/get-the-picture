# AGENTS.md

## Project

More Than Meets the AI is a CSC173 multiplayer drawing game where humans race a transformer AI to recognize sketches. Research focuses on recognition through shared semantic and cultural visual references.

- `apps/web/`: implemented Next.js/TypeScript canvas frontend; room entry, chat, scores, and AI panels are local fixtures.
- `research/guesser-evaluation/`: uv-managed Python/Jupyter environment for Evaluation & Inference; the current scaffold does not include an evaluator, inference service, trained weights, or measured results.
- Planned backend: NestJS + Socket.IO, FastAPI inference, PostgreSQL/Prisma. One authoritative game process holds active matches in memory; no Redis.

## Read first

- `README.md`, `CONTEXT.md`, `SYSTEM-DESIGN.md`: overview, vocabulary, and current rules.
- `docs/BACKEND-SCORING-PLAN.md`: required before scoring or turn-lifecycle changes.
- `docs/FRONTEND-BASE-SCOPE.md` and `docs/FRONTEND-IMPLEMENTATION-PLAN.md`: frontend scope and design. Reuse existing drawing libraries and assets in `docs/design-system/`.

## Working rules

- Default to individual free-for-all: one rotating drawer, one shared canvas, and personal solves/scores. A first human solve does not end the turn. Team mode requires explicit selection.
- Keep secret targets and accepted correct answers hidden from unsolved guessers until reveal. Referee flags are advisory; incidental writing on depicted objects is allowed.
- Decide routine implementation details independently. Ask the user about unresolved gameplay or architecture choices before implementing them.
- Explain key reasoning clearly, update affected docs when behavior changes, and distinguish fixtures, planned features, implemented behavior, and verified results.

## Development and validation

Use Node.js 24 and npm. Run frontend commands from `apps/web/`:

```sh
npm ci
npm run dev
```

For frontend code changes, run the relevant checks: `npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`. Use `npm run test:e2e` for affected browser flows; it requires a production build and installed Google Chrome. Report what ran and any validation limits.

For the cross-platform research workspace, use `uv sync --project research/guesser-evaluation --locked` and run notebooks from that uv environment. Keep Python requirements compatible with Windows and Linux; do not commit datasets, checkpoints, or machine-specific CUDA paths. See `research/guesser-evaluation/README.md`.
