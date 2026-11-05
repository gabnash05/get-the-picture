# Guesser inference

Model loading and prediction service code belongs here.

This is a placeholder; no inference implementation is included yet.

Use the sibling [data package](../data/README.md) for prepared data and shared preprocessing. Data-pipeline checks remain in `../data/tests/`.

## Required libraries

Use timm and the existing checkpoint APIs to reconstruct/load the trained model, PyTorch eval/inference_mode for predictions, and FastAPI/Pydantic/Uvicorn for the service. Reuse the exact selected data preprocessor. Implement only the game's queue/checkpoint/version/pass policy around those libraries.

See the [library guide](../LIBRARIES.md) and [implementation rules](../AGENTS.md). These choices do not mean the model packages or service are installed yet.
