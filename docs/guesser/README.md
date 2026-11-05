# Guesser planning package

The two outputs below were reviewed and accepted in the Guesser planning session on 5 November 2026. They are preserved as reviewed.

- [Complete model and data plan](guesser-model-plan.md): responsibilities, all-345-category Quick, Draw! preparation, partial-view generation, ViT-Tiny adaptation, validation, and inference requirements.
- [Interactive workflow visualization](guesser-flow.html): an offline-capable HTML companion with a real timestamped-drawing replay, background-fill illustration, and a dedicated model-validation section. Open it in a browser; its Markdown download link points to the sibling file.

These are implementation plans. No trained weights, full dataset download, model accuracy result, or production AI service is included.

## Integration with the current game contract

The reviewed outputs contain team-oriented runtime examples. The repository's [system design](../../SYSTEM-DESIGN.md), [glossary](../../CONTEXT.md), and [backend scoring plan](../BACKEND-SCORING-PLAN.md) define **individual free-for-all as the default**. Apply that default when implementing the Guesser:

- One shared canvas and one logical AI race serve the drawing turn. Each human guesser has an independent solve and score.
- A first human solve does not cancel drawing or the remaining AI opportunities while eligible unsolved humans remain. Closing a turn and stopping the AI after its own correct answer follow the backend contract.
- Checkpoint observation acknowledgements come from active unsolved human guessers. The secret target and human answer text remain outside AI input.
- Use match, drawing-turn/canvas, generation, checkpoint, and job identities. A team ID is relevant only when optional team mode is explicitly selected.
- Treat the reviewed three-team scenario as a concurrent-stream capacity test or an optional-mode scenario, rather than the individual-mode default.
- Scoring and service-failure eligibility remain authoritative in NestJS, not in the model service.

The data/model experiment remains unchanged: all 345 Quick, Draw! classes, original-drawing splits before partial views, shape-based preprocessing with a fill/background validation pilot, and a controlled complete-only versus partial-training comparison. This direct-depiction Guesser plan does not establish recognition of indirect semantic or cultural visual references from the broader research design.
