# Domain glossary

## Team
A group of at least two human players competing together. Players agree on the number of teams and the size of each team; teams may have unequal sizes. Each round has one drawer and all remaining teammates guessing.

## Drawer
The single team member assigned to draw in a round. The drawer knows the secret prompt and represents it through a sketch.

## Human guesser
Any non-drawing member of a team, who tries to identify the secret prompt from that team's evolving sketch and the official hints. Human guessers may keep submitting guesses until the team solves, forfeits or reaches the shared time limit.

## AI guesser
The transformer-powered competitor assigned to a team's drawing challenge. It tries to identify the prompt from that team's evolving sketch and the same official hints available to humans, with a limited number of guesses. Its intended gameplay difficulty is credible but beatable, with uncertain race outcomes.

## Shared prompt
The same randomly selected secret drawing target assigned to all competing teams, replaced with a fresh prompt each round.

## Parallel team challenges
Simultaneous drawing-and-guessing challenges in which each team produces its own sketch of the shared prompt and its human guessers race that team's AI guesser.

## Team canvas
The drawing surface used by one team; opposing human players cannot see it during an active challenge.

## Opponent progress
The public status of the other teams' challenges, such as still guessing or solved, without revealing their canvases or human guess text during play.

## Human solve
A correct guess submitted by a human guesser on a team.

## Speed points
Points provisionally credited once to a team for its first correct human guess, based on how quickly that guess is submitted. The team can earn these points even if its AI guessed correctly earlier. They count toward the match when the round is finalized.

## Beat-the-AI bonus
Additional points provisionally credited once to a team when its first correct human guess precedes its AI's correct answer. The bonus is finalized at round end; an AI guesser outage that prevents required attempts disables it for every team in that round.

## AI guess
An answer proposed by an AI guesser. Its text stays hidden from human players during the active challenge and is revealed in the replay.

## AI progress
The visible status of an AI guesser's attempt to identify the prompt, without disclosing its guess text during play.

## Replay
The end-of-round retrospective that reveals the AI's guesses and recognition timing alongside the drawing's development.

## Visual strategy
Any drawing-based way to communicate the shared prompt, subject to the prohibition of written answer clues.

## Written answer clue
A prohibited written hint used to communicate the prompt, such as spelling the answer, writing initials or a translation, or supplying letter-by-letter hints.

## AI referee
The separate transformer-powered referee that publicly warns players about suspected written answer clues. Its flags are advisory, and players resolve disputes.

## Incidental writing
Permitted writing that belongs to an object being depicted, rather than being used as a written hint to communicate the prompt.

## Referee flag
A public warning identifying a team's suspected written-clue violation while preserving canvas privacy. It calls attention to the incident without requiring removal or imposing an automatic penalty.

## Referee dispute
A disagreement about whether flagged content is a prohibited written answer clue or permitted drawing content, resolved by the players.

## Team challenge
One team's drawing-and-guessing race within a round. It ends on that team's first correct human guess, a team forfeit, or expiry of the shared timer. Ending the challenge stops drawing and AI guessing for that team.

## Round
The competing teams' simultaneous challenges using the same randomly selected prompt and a shared time limit. It ends when all teams have solved, forfeited or reached the time limit, followed by finalization, reveal and replay.

## Role rotation
Drawer duty passes through the members of each team in turn after every round; all other teammates guess. The fixed match length may end partway through a rotation, so drawing-turn counts within a team need not be equal.

## Match
A contest among player-agreed teams over a player-agreed fixed number of rounds, won by the team with the highest finalized accumulated score from speed points and beat-the-AI bonuses.

## AI guess budget
The maximum number of guesses available to an AI guesser in a team challenge. Every team's AI receives the same budget; human guesses have no fixed cap.

## AI guess checkpoint
A scheduled opportunity for an active AI guesser to submit a guess during a round. All teams' AIs use the same fixed checkpoint schedule.

## Prompt pool
The collection of familiar, everyday drawable concepts from which shared prompts are randomly selected. Its vocabulary follows the style of ordinary skribbl.io prompts and is intended to cover concepts the AI could reasonably recognize.

## Official hints
Word length and letters progressively revealed during a round. Human and AI guessers receive the same hints on the same schedule across all teams.

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
The player-agreed number of teams and number of human players on each team. The notation 3v2v4 describes three teams containing three, two, and four human players respectively. Equal team sizes are not required.

## Team solve
The first correct guess submitted by any of a team's human guessers. It completes the team's challenge and records one provisional team result, including any eligible beat-the-AI bonus. Other teammates do not earn additional solve scores for the same prompt.

## Reconnect grace
A bounded opportunity to restore at least one eligible human guesser when a team has no active guesser. Connected teammates otherwise keep playing, and other teams and the common round clock continue.

## Team forfeit
The end of an active team challenge when no eligible human guesser recovers before its reconnect grace expires. One absent member does not forfeit a team that still has an active guesser. The forfeited team earns no solve score for that challenge; other teams continue.

## Round finalization
Confirmation of the round's team scores and AI-bonus eligibility, after which those results count toward the match total.

## Voided round
A round whose competitive history cannot be verified and whose provisional scores therefore do not count. It is retried at the same match position with a fresh prompt, without advancing the drawer rotation.

## AI guesser unavailable
A required AI guess that cannot be completed because of a service fault, distinguished from an incorrect answer or normal cancellation. It disables AI bonuses for all teams in the affected round while preserving human speed points.
