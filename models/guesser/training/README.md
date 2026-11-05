# Guesser training

Training and fine-tuning code belongs here.

This is a placeholder; no training implementation is included yet.

Use the sibling [data package](../data/README.md) for prepared data and shared preprocessing. Data-pipeline checks remain in `../data/tests/`.

## Required libraries

Use timm for the pretrained ViT-Tiny and its 345-class head; Lightning Trainer/Module/DataModule and callbacks for the training loop, device/precision handling, resume, checkpoint selection and logs; PyTorch Dataset/DataLoader for batches; torchvision v2 for ordinary augmentation; PyTorch loss/optimizer/schedulers and TorchMetrics for standard learning operations and scores. Keep custom code to data adaptation and the experiment protocol.

See the [library guide](../LIBRARIES.md) and [implementation rules](../AGENTS.md). These choices do not mean the model packages or service are installed yet.
