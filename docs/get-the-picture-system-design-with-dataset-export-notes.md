# Dataset export architecture copy

Created 1 November 2026 from `get-the-picture-system-design.excalidraw`.
The original editable diagram and original PNG have not been modified.

## Changes

- Preserved all 45 original element IDs, the monochrome handwritten style,
  browser/server grouping, and existing core components. Expanded the layout
  only to fit the new modules and readable connector gutters.
- Kept the renderer on the AI and Rendering Server. A versioned checkpoint is
  rendered once, with decoded pixels used for inference and a separately
  encoded PNG returned to the game backend for background archival.
- Added a Background Archive Writer inside the NestJS backend. It batches
  gameplay records and checkpoint artifacts into PostgreSQL. The AI host has
  no direct game-database connection.
- Added a Dataset Export Module inside the same backend. It packages saved
  images and records as PNGs plus JSONL through an authorized HTTP download.
  Routine export does not render those images again.
- Added an offline review, dataset preparation, fine-tuning and evaluation
  workflow. Its dashed boundary is a workflow, not a third permanent host.
- Updated the backend label to NestJS and routed Next.js page requests through
  the existing reverse proxy, consistent with the clarified design.

## Assumptions and boundaries

- In-memory image means decoded pixels on the AI host. Depending on the worker
  implementation, use a same-process image object or an agreed worker-buffer
  transfer. The diagram does not imply sharing a JavaScript object across hosts.
  The concrete worker IPC mechanism remains an implementation choice.
- Archive transfers include checkpoint/input identity and version metadata so
  an exported image can be linked to the correct drawing, hints and outcome.
  Background archival does not block the live drawing/inference path; a complete
  export includes only saved, verified records and artifacts.
- Preserve stroke history for replay and additional offline snapshots. Extra
  rendering uses the same renderer with lower priority than live jobs.
- Secret targets are training output labels and remain outside model inputs.
  Related drawing/session frames stay together when making dataset splits.
- Fine-tuning runs outside gameplay on the AI machine or another available
  training environment. Model selection follows evaluation; no training gain
  or performance improvement is claimed by this diagram.

## Verification

- Copied `.excalidraw` passed the installed Excalidraw validator.
- All original element IDs were retained; bindings reference existing elements.
- Component overlap and connector geometry checks passed. Native font
  measurements reported no overflowing text labels.
- PNG and SVG were exported locally using `@excalidraw/excalidraw` 0.18.1 and
  visually inspected in an isolated Chrome session. No scene was uploaded to
  an external editor. The PNG includes the full diagram.
- Original source SHA-256:
  `9712d15ff560a8616fb86ca26002cc34eab4ff8c3127012dfe1663dbe82aa82a`.

Open `get-the-picture-system-design-with-dataset-export.excalidraw` in Excalidraw to edit it.
The SVG is a zoomable preview and the PNG is suitable for sharing.
