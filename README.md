# More Than Meets the AI

A transformer-powered multiplayer drawing game for an intelligent-systems class project.

**The default mode is individual free-for-all, not a team game.** One player draws on a shared canvas while every other player guesses for their own score and races the same AI guesser. The drawer and guessers are individual competitors, not teammates. Drawer duty rotates through the room's players; the highest finalized individual total wins.

Each human guesser can solve the prompt independently. A first correct human guess does not end the drawing turn: drawing, remaining human guesses and eligible AI attempts continue. The turn ends when all eligible human guessers have solved or the timer expires. An AI solve stops its own further guessing, while humans can still solve for points. Human and AI guessers receive the same official word-length and revealed-letter hints; AI answer text stays hidden until reveal/replay.

The scoring plan distinguishes the roles. Each guesser earns speed-based points, with a stronger before/after-AI adjustment applied to that person's own solve. The drawer earns ordinary points for successful human recognition plus a smaller, capped bonus based on humans beating the AI. The AI's answer earns the drawer no ordinary drawing points. AI-first reduces points earned on that turn; it does not deduct previously earned totals or erase an earlier human's achievement. Exact weights remain to be tuned. See [the backend scoring implementation plan](docs/BACKEND-SCORING-PLAN.md).

Any visual strategy is allowed; written answer clues are prohibited, while incidental writing on objects is allowed. A separate transformer referee flags suspected written clues. Flags are advisory, and players resolve disputes.

## Canvas frontend

The working canvas base is in [apps/web](apps/web). It includes guest names and customizable characters, local create/join flow, brush and eraser tools, region fill, undo/redo/Clear, and console drawing batches targeting 33 ms. The game panels and chat are local fixtures while the backend is developed separately.

See the [frontend run/build instructions](apps/web/README.md), [implementation plan](docs/FRONTEND-IMPLEMENTATION-PLAN.md), and [temporary UI scope](docs/FRONTEND-BASE-SCOPE.md). Build `apps/web` with `npm run build`; its `out/` directory can be served by a static host. No hosting provider has been configured by this implementation.

## Guesser data and evaluation

The agreed [models layout](models/README.md) separates Guesser data, training, inference, evaluation and checkpoints from Referee work. The [data package](models/guesser/data/README.md) uses Python 3.13 and uv: numbered stages download/clean/sample, prepare splits, optionally preview and export with one data audit. Timed image creation uses the shared foreground/edges preprocessors; no approvals or freeze step are required. See the [runbook](models/guesser/data/RUNBOOK.md).

The [evaluation workspace](models/guesser/evaluation/README.md) now contains the incoming Python 3.12/uv notebook scaffold. It has environment-check code, not an evaluator, inference service, trained checkpoint or accuracy result. Training/batching and serving remain their owners' next work. No full dataset download was run for this refactor.

## Game modes

**Individual is the default when a room or match has no explicit mode selection.** It uses one drawer, one shared canvas, individual solve records and an individual leaderboard. Do not implement it by grouping everyone into one team. The temporary frontend's sample team panels are fixtures, not the default gameplay contract.

Team play is a separate optional mode that must be explicitly selected if implemented. The earlier agreed formats remain valid for that mode: `2v2`, `2v2v2`, `3v3`, `3v3v3`, `2v3`, and `3v2v4`. Team mode can retain parallel private canvases and a first-human-solve team result; those rules must not leak into individual mode.

## Recovery and availability

- NestJS accepts live events in memory and broadcasts them immediately; PostgreSQL archival runs asynchronously. A restart voids unfinished drawing turns and retries the same drawer/turn position with a fresh prompt while preserving committed prior results.
- In individual mode, connected players continue after another player disconnects. An individual solve already accepted is retained; disconnecting does not merge or forfeit everyone else's result. Exact no-guesser grace and unresolved-player closure rules must be specified before backend implementation.
- If a required AI attempt is unavailable because of a service fault, preserve human-only scoring and neutralize the affected turn's AI-derived bonuses and reductions for all players, including the drawer's AI bonus. Referee outages leave advisory flagging unavailable. Readiness-related missed checkpoints require an explicit individual-mode policy; do not reuse a team-wide bonus penalty by accident.
- Scores remain provisional until required records and results commit to PostgreSQL. Missed guesses, service failures and normal cancellations are distinct. A voided turn does not consume a drawing turn or advance rotation.

## Architecture

The proposed stack is **Next.js** for the web application, **NestJS + Socket.IO** for the authoritative game backend, **FastAPI** for inference, and **PostgreSQL + Prisma** for saved records. Active matches live in one game process's memory, with background archival. See [SYSTEM-DESIGN.md](SYSTEM-DESIGN.md), [the architecture preview](docs/get_the_picture_system_design.png), and [the editable Excalidraw source](docs/get-the-picture-system-design.excalidraw). The frontend canvas base is implemented. The backend, inference services, and production deployment remain a design baseline; no deployment or gameplay/model benchmark is claimed.

## Research evaluation workspace

`models/guesser/evaluation/` is a uv-managed, cross-platform Python/Jupyter workspace for auditing held-out inputs, evaluating frozen model checkpoints, measuring inference latency, and preparing the live inference interface. The environment and smoke-check notebook are set up; the evaluator, inference service, trained weights, and performance results remain future work. See its [setup, usage, and notebook merge-conflict guide](models/guesser/evaluation/README.md).

## Project focus

The current primary research question is how well humans and a transformer-powered AI identify intended targets from sketches that use shared semantic and cultural visual references. Recognition speed as a sketch develops is secondary.

A separate sketch-focused comparison will examine recognition of the same incomplete drawings, independently of the party game's letter hints and AI guessing handicap. The party game retains those hints and handicaps. Private visual codes remain legal during gameplay but are excluded from the main research comparison.

Target correctness and reference interpretation are distinct outcomes. Detailed interpretation analysis, including collecting and scoring explanations of the visual cue and its connection to the target, is deferred to future work. The current class-project scope should keep player onboarding brief and avoid extensive player training.

The intended AI opponent is credible but beatable, with uncertain race outcomes. These are project aims; recognition performance and gameplay balance have not been validated. The original pitch also asks whether an AI competitor makes play more engaging; increased engagement is not an established result.

## Vocabulary

See [CONTEXT.md](CONTEXT.md) for the domain glossary.
