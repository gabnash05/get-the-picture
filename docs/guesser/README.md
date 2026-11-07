# Guesser planning package

The two outputs below were reviewed and accepted in the Guesser planning session on 5 November 2026. The model/evaluation design is retained; its data sections now follow the slimmer numbered workflow.

- [Complete model and data plan](guesser-model-plan.md): responsibilities, all-345-category Quick, Draw! preparation, partial-view generation, ViT-Tiny adaptation, validation, and inference requirements.
- [Interactive workflow visualization](guesser-flow.html): an offline-capable companion for the six numbered data stages, loader route, worked timestamp example and memory illustration. Full model/evaluation requirements remain in the Markdown plan.

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


## Implemented data tooling

The [Guesser data package](../../models/guesser/data/README.md) uses Python 3.13 and uv with six literal numbered stages: download, prepare, optional preview, export, loader and image creation. Real defaults live in Python settings. Production remains the full-source default; medium and small stop after collecting prefix reserves and prepare 2,000 and 500 originals/class, respectively, while preserving all 345 labels. There are no approval CSVs, sign-offs, code/document fingerprints, freeze step or global download budget. See the [current runbook](../../models/guesser/data/RUNBOOK.md).

The [training package](../../models/guesser/training/README.md) implements Lightning + timm A/B fine-tuning on prepared small/medium/production data. The [evaluation scaffold](../../models/guesser/evaluation/README.md) keeps its separate Python 3.12 lock; stage-wise held-out metrics and the inference service remain Validation/Inference owner work. Historical data reports/ZIPs are retained as historical evidence rather than rebuilt by this refactor.

## Library implementation guidance

The [current library map](../../models/guesser/LIBRARIES.md) requires timm, Lightning, PyTorch DataLoader, torchvision, TorchMetrics and FastAPI/Pydantic for the corresponding standard tasks. It supplements the retained reviewed plan; its uv setup requirement supersedes the historical pip commands in that plan. Training code and the model `pyproject.toml`/`uv.lock` are in place; inference service code remains for its owner.
