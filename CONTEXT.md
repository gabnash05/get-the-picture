# Domain glossary

Default-mode terminology updated 4 November 2026. Team-specific terms below apply only to the separate optional mode.

## Individual mode
The default free-for-all format: one rotating drawer, one shared canvas, independently competing human guessers, a shared AI benchmark and personal scores. Drawer and guessers are not teammates.

## Drawing turn
One drawer's opportunity to depict one secret target while other eligible humans and the AI guess. It continues after the first human solve and ends when all eligible humans have solved or the deadline expires, subject to explicit abandonment rules.

## Personal solve order
The authoritative order of an individual's correct answer relative to the AI's first accepted correct answer. An AI answer accepted later does not erase that human's earlier success.

## After-AI reduction
A smaller reward for a correct human solve accepted after the AI solved. It affects that turn's earnings, not previously earned totals; numeric weights remain to be tuned.

## Drawer recognition points
The drawer's ordinary personal reward for humans correctly identifying the drawing. AI recognition and simply keeping everyone confused do not earn it.

## Drawer AI bonus
A smaller, capped reward tied to the share of eligible humans who recognized the drawing before the AI. It supplements successful human communication and does not replace ordinary drawer recognition points.

## Team
In optional team mode, a group of at least two human players competing together. Team sizes may differ. Individual mode has no human teams, including no implicit team containing the whole room.

## Drawer
The player assigned to draw the secret target during a drawing turn. In default individual mode the drawer competes for their own points and is not a teammate of the guessers.

## Human guesser
An eligible non-drawer who identifies the target from the evolving canvas and official hints. In individual mode each guesser has an independent result; their first correct answer ends only their own guessing, not the whole turn.

## AI guesser
The transformer-powered competitor observing the permitted canvas and hints with a capped guess budget. Default individual play has one logical AI race for the shared drawing turn; optional team mode assigns a logical competitor per team canvas.

## Shared prompt
The secret target depicted in a drawing turn. In optional parallel team mode, all teams receive the same fresh target for that round.

## Parallel team challenges
Optional team-mode races played simultaneously on private team canvases. They are not the default individual mode.

## Team canvas
A private canvas belonging to one team in optional team mode. Individual mode instead uses one shared canvas visible to all room players.

## Opponent progress
Visible solve/AI status without disclosing the hidden answer. Default individual play shows personal progress; optional team play also shows opposing team status while hiding private canvases.

## Human solve
A human's first correct accepted guess for a drawing turn. In individual mode it creates that player's personal result; it never solves the turn for everyone else.

## Speed points
Turn points based on how quickly an individual human solves. The personal before/after-AI adjustment changes that turn reward. Optional team mode instead credits one team speed result at its first human solve.

## Beat-the-AI bonus
An AI-related positive score component when a human solves before the AI's accepted correct answer. Default guesser credit is personal; the drawer's separate bonus is smaller and capped. Optional team mode retains one team bonus. Required AI-service failure neutralizes default-turn AI bonuses and reductions while retaining human-only scoring.

## AI guess
An answer proposed by the AI. Actual answer text remains hidden from unsolved humans until reveal/replay. It is never a human solve or ordinary drawer-score contribution.

## AI progress
The visible status of an AI guesser's attempt to identify the prompt, without disclosing its guess text during play.

## Replay
The retrospective revealing the drawing's development, human/AI solve timing, attempts and flags after the drawing turn ends.

## Visual strategy
Any drawing-based way to communicate the shared prompt, subject to the prohibition of written answer clues.

## Written answer clue
A prohibited written hint used to communicate the prompt, such as spelling the answer, writing initials or a translation, or supplying letter-by-letter hints.

## AI referee
The separate transformer-powered referee that publicly warns players about suspected written answer clues. Its flags are advisory, and players resolve disputes.

## Incidental writing
Permitted writing that belongs to an object being depicted, rather than being used as a written hint to communicate the prompt.

## Referee flag
An advisory warning of a suspected written clue, with disputes resolved by players. Optional-team warnings preserve opposing-canvas privacy; flags do not automatically deduct scores.

## Referee dispute
A disagreement about whether flagged content is a prohibited written answer clue or permitted drawing content, resolved by the players.

## Team challenge
In optional team mode, one team's race ending at its first correct human solve, forfeit or timeout. It is not the default individual turn-completion rule.

## Round
A grouping of drawing turns in the match schedule; its exact UI/counting convention must be made explicit during backend planning. Optional parallel team mode uses a round for its simultaneous shared-prompt challenges. A drawing turn has its own identity and completion rule.

## Role rotation
In individual mode, drawer duty passes through the room players after a completed drawing turn. Optional team mode rotates drawers within each team. An individual solve alone never advances rotation.

## Match
A scheduled contest won by the human with the highest finalized personal total in default individual mode. Optional team mode uses finalized team totals instead.

## AI guess budget
The maximum number of AI guesser attempts available for a drawing turn, with fixed checkpoints. Humans have no fixed guess cap. Optional parallel team challenges use equal budgets per logical AI.

## AI guess checkpoint
A scheduled opportunity to infer from a frozen permitted drawing and hint state. In default play opportunities continue after the first human solve while other eligible humans remain unsolved.

## Prompt pool
The collection of familiar, everyday drawable concepts from which shared prompts are randomly selected. Its vocabulary follows the style of ordinary skribbl.io prompts and is intended to cover concepts the AI could reasonably recognize.

## Official hints
Word length and progressively revealed letters. Human and AI guessers receive the same permitted hint state and schedule for their drawing turn.

## Sketch-focused comparison
A research comparison of human and AI recognition of the same incomplete sketches, separate from the party game's timed letter hints and AI guessing handicap.

## Recognition speed
How early a human or AI supplies a correct identification during a drawing's development. It is a secondary research outcome and does not directly establish an internal moment of understanding.

## Direct depiction
A sketch that represents the target itself.

## Indirect visual reference
A sketch that communicates the target through a related object, scene, character, or symbol, rather than depicting the target itself.

## Shared association
A semantic or cultural connection that an interpreter may recognize without a private agreement with the drawer, such as cow to milk or Minion to banana.

## Private visual code
A prearranged mapping between a visual mark and a meaning known to particular players. It is permitted as a visual strategy in the game but excluded from the main sketch-focused comparison.

## Target correctness
Whether a guess correctly identifies the intended prompt, considered separately from an explanation of the visual reference.

## Reference interpretation
An account of the recognized visual cue and its semantic or cultural connection to the target. It is distinct from simply naming the target correctly.

## Team format
An explicitly selected optional-mode arrangement such as 2v2 or 3v2v4. It is never inferred from an individual room or used as the default.

## Team solve
The first teammate correct guess in optional team mode, closing that team's challenge and creating one team result. This concept must not replace per-player solves in individual mode.

## Reconnect grace
A bounded chance for a disconnected participant to return and synchronize. Individual solves remain personal; exact no-guesser/unresolved-player rules need an explicit default-mode policy. Optional team-mode no-guesser grace can forfeit only the affected team challenge.

## Team forfeit
An optional team-mode outcome when an active challenge has no recovered eligible human guesser before grace expires. It does not apply to all individual players when one person disconnects.

## Round finalization
Confirmation of the applicable turn/round results after their required records are saved. Individual totals use committed per-player results; team totals are mode-specific.

## Voided round
An unverifiable competitive turn/round whose provisional scores are discarded. Default play retries the same drawing-turn position and drawer with a fresh target; prior committed personal results remain.

## AI guesser unavailable
A required AI attempt missing because of a service fault, distinct from a wrong guess or normal cancellation. Default play uses human-only turn scoring with all AI adjustments neutralized; optional team mode removes AI bonuses across its affected round.
