# More Than Meets the AI - canvas base

A local frontend for testing the drawing canvas and outgoing event batches. Built from the approved Lemon Crayon preview.

## Run locally

Use Node.js 24 and npm. The browser tests also require an installed Google Chrome.

```sh
npm ci
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open http://localhost:3000. Choose a name and character, then create or join a room. Room entry is local to your browser; codes do not connect players yet.

## Static build and preview

```sh
npm run build
npm run preview
```

Open http://127.0.0.1:3100. The `out/` directory contains the portable site. A static host must serve directory index files (including `room/index.html`) and worker assets from the same origin. Set the host's project root to `apps/web`, build command to `npm run build`, and output directory to `out`. Hosting-provider setup is separate work.

## Drawing controls

- Brush, pixel eraser, and region-fill bucket; palette/custom colors and brush size 2-40.
- Undo/redo applies to strokes, erasing, fills, and Clear; history retains up to 20 actions within a 64 MiB bitmap budget.
- B / E / F select a tool. Ctrl/Cmd+Z undoes; Ctrl/Cmd+Shift+Z or Ctrl/Cmd+Y redoes. Text fields keep ordinary editing behavior.
- Drawing uses fixed 1024 x 768 logical coordinates and scales to your viewport without resetting its bitmap.

Open browser DevTools Console to inspect `[drawing:batch]` objects while drawing. Nonempty batches target 33 ms, with immediate final stroke and edit-command flushes. Logs include actual intervals, IDs, sequence ranges, counts, UTF-8 bytes, and operation payloads. These are console-only outgoing operations; no backend acceptance is simulated.

The local profile is remembered. Refreshing this base starts a blank drawing. Final-game persistence is a separate backend requirement.

## Verification

```sh
npm run typecheck
npm run lint
npm test
npm run build
npm run test:e2e
```

Browser checks use installed Google Chrome through Playwright and test the exported production build. If Chrome is unavailable, install it or install Playwright Chromium and adjust the test project channel.

The game panels and local chat are fixtures. After canvas validation, the user will replace or substantially revise the UI. The scope and motion contracts live in the game repository's `docs/FRONTEND-BASE-SCOPE.md`, `docs/FRONTEND-IMPLEMENTATION-PLAN.md`, and `docs/design-system/LOGIN_MOTION.md`.
