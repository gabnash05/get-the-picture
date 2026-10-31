# Get the Picture?

A transformer-powered multiplayer drawing game for an intelligent-systems class project.

Teams compete simultaneously on separate canvases using the same randomly selected, familiar everyday prompt. Each team has one drawer per round, while every other teammate guesses and races a transformer-powered AI assigned to that team's challenge. The first correct human guess solves the challenge for the whole team and earns one speed-based team score, with a bonus for beating its AI. Every team's AI has the same guess cap and fixed checkpoints; human teammates can keep guessing until the team solves or the shared time limit expires. Human and AI guessers receive the same word-length and progressively revealed-letter hints.

Canvases and human guesses stay private to their team during play, while opponent progress is visible. AI guess text is saved for the replay. Any visual strategy is allowed; written answer clues are prohibited, while incidental writing on objects is allowed. A separate transformer referee publicly flags suspected written clues. These flags are advisory, and players resolve disputes.

Each team stops drawing and AI guessing on its first correct human guess. The round ends when all teams have solved, forfeited, or reached the time limit. The reveal and replay follow. Drawer duty rotates through each team's members after every round. Players agree on a fixed match length; it need not be even or complete full drawing rotations. Short matches may give some teammates an extra drawing turn. The highest finalized total team score wins the match.

## Team format

Players agree on the number of teams and the number of human players per team before the match. There are at least two teams, and each team needs at least two players for drawing and human guessing. Team sizes may be equal or unequal; the concept does not prescribe a fixed maximum number of teams or players per team.

Valid examples include `2v2`, `2v2v2`, `3v3`, `3v3v3`, `2v3`, and `3v2v4`. In `3v2v4`, three teams have three, two, and four human players respectively. Unequal sizes are allowed by player agreement.

## Recovery and availability

- NestJS accepts live events in memory and broadcasts them immediately; PostgreSQL archival runs asynchronously. A game-server restart voids unfinished rounds. Retry with a fresh prompt using saved match setup and committed prior-round results; transparent active-match failover is outside the baseline.
- Connected teammates keep playing after a disconnect. A team gets reconnect grace when it has no active human guesser; it forfeits only if no guesser recovers within that grace. Other teams and the common round clock continue.
- If an AI guesser outage prevents a required attempt, keep human speed points and disable the AI bonus for every team in that round. A checkpoint missed because human clients were not ready removes only that team's bonus. Referee outages leave advisory flagging unavailable.
- Round points and bonuses stay provisional until the round's required records are saved and its result commits to PostgreSQL. A normal cancellation after a solve or forfeit is not an AI outage. A voided round does not consume a match round or advance the drawer rotation.

## Architecture

The proposed stack is **Next.js** for the web application, **NestJS + Socket.IO** for the authoritative game backend, **FastAPI** for inference, and **PostgreSQL + Prisma** for saved records. Active matches live in one game process's memory, with background archival. See [SYSTEM-DESIGN.md](SYSTEM-DESIGN.md), [the architecture preview](docs/get_the_picture_system_design.png), and [the editable Excalidraw source](docs/get-the-picture-system-design.excalidraw). This is documentation, not an implemented or benchmarked deployment.

## Project focus

The current primary research question is how well humans and a transformer-powered AI identify intended targets from sketches that use shared semantic and cultural visual references. Recognition speed as a sketch develops is secondary.

A separate sketch-focused comparison will examine recognition of the same incomplete drawings, independently of the party game's letter hints and AI guessing handicap. The party game retains those hints and handicaps. Private visual codes remain legal during gameplay but are excluded from the main research comparison.

Target correctness and reference interpretation are distinct outcomes. Detailed interpretation analysis, including collecting and scoring explanations of the visual cue and its connection to the target, is deferred to future work. The current class-project scope should keep player onboarding brief and avoid extensive player training.

The intended AI opponent is credible but beatable, with uncertain race outcomes. These are project aims; recognition performance and gameplay balance have not been validated. The original pitch also asks whether an AI competitor makes play more engaging; increased engagement is not an established result.

## Vocabulary

See [CONTEXT.md](CONTEXT.md) for the domain glossary.
