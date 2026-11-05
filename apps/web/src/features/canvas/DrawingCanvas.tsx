"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import type Atrament from "atrament";
import {
  CANVAS_HEIGHT,
  CANVAS_WIDTH,
  type CanvasOperation,
  type CanvasPoint,
  type DrawingCanvasHandle,
  type DrawingCanvasProps,
} from "../../contracts/drawing";
import { BitmapHistory, type Snapshot } from "./history";
import styles from "./DrawingCanvas.module.css";

const uid = () => crypto.randomUUID();

type Engine = { undo(): void; redo(): void; clear(): void; finish(): void };
const DrawingCanvas = forwardRef<DrawingCanvasHandle, DrawingCanvasProps>(
  function DrawingCanvas(props, ref) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const propsRef = useRef(props);
    const engineRef = useRef<Engine | null>(null);
    propsRef.current = props;
    useImperativeHandle(
      ref,
      () => ({
        undo: () => engineRef.current?.undo(),
        redo: () => engineRef.current?.redo(),
        clear: () => engineRef.current?.clear(),
      }),
      [],
    );

    useEffect(() => {
      const canvas = canvasRef.current!;
      const context = canvas.getContext("2d", { willReadFrequently: true })!;
      const history = new BitmapHistory();
      let alive = true,
        busy = false,
        hasInk = false;
      let artist: Atrament | undefined;
      let worker: Worker | undefined;
      let queue: (() => void)[] = [];
      let active:
        | {
            pointerId: number;
            actionId: string;
            before: Snapshot;
            last: CanvasPoint;
            previousX: number;
            previousY: number;
            started: number;
          }
        | undefined;
      const status = () => {
        canvas.dataset.ready = String(!!artist);
        canvas.setAttribute("aria-busy", String(!artist || busy));
        propsRef.current.onStatusChange?.({
          canUndo: history.canUndo,
          canRedo: history.canRedo,
          busy: !artist || busy,
          hasInk,
        });
      };
      const emit = (op: CanvasOperation) => propsRef.current.onOperation(op);
      const base = (actionId: string) => ({
        opId: uid(),
        actionId,
        at: Date.now(),
      });
      const snapshot = (): Snapshot => ({
        image: context.getImageData(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT),
        hasInk,
      });
      const detectInk = () => {
        const pixels = context.getImageData(
          0,
          0,
          CANVAS_WIDTH,
          CANVAS_HEIGHT,
        ).data;
        for (let i = 0; i < pixels.length; i += 4)
          if (
            pixels[i + 3] &&
            (pixels[i] !== 255 ||
              pixels[i + 1] !== 255 ||
              pixels[i + 2] !== 255)
          )
            return true;
        return false;
      };
      const restore = (s: Snapshot) => {
        context.putImageData(s.image, 0, 0);
        hasInk = s.hasInk;
      };
      const point = (e: PointerEvent, started: number): CanvasPoint => {
        const r = canvas.getBoundingClientRect();
        return {
          x: Math.max(
            0,
            Math.min(
              CANVAS_WIDTH - 1,
              ((e.clientX - r.left) * CANVAS_WIDTH) / r.width,
            ),
          ),
          y: Math.max(
            0,
            Math.min(
              CANVAS_HEIGHT - 1,
              ((e.clientY - r.top) * CANVAS_HEIGHT) / r.height,
            ),
          ),
          time: Math.max(0, performance.now() - started),
          pressure: e.pressure || 0.5,
        };
      };
      const external = (p: CanvasPoint) => ({
        x: (p.x * canvas.offsetWidth) / CANVAS_WIDTH,
        y: (p.y * canvas.offsetHeight) / CANVAS_HEIGHT,
      });
      const finish = () => {
        if (!active || !artist) return;
        const s = active;
        active = undefined;
        const p = external(s.last);
        artist.endStroke(p.x, p.y);
        history.push(s.actionId, s.before);
        hasInk = detectInk();
        emit({ ...base(s.actionId), type: "stroke.end", point: s.last });
        if (canvas.hasPointerCapture(s.pointerId))
          canvas.releasePointerCapture(s.pointerId);
        status();
      };
      const command = (run: () => void) => {
        finish();
        if (busy) queue.push(run);
        else run();
      };
      const drain = () => {
        while (!busy && queue.length && alive) queue.shift()?.();
      };
      const fill = (p: CanvasPoint, color: string) => {
        if (!worker) {
          try {
            worker = new Worker(new URL("./fill.worker.ts", import.meta.url));
          } catch {
            propsRef.current.onError?.("Fill worker is unavailable.");
            return;
          }
        }
        const actionId = uid();
        const before = snapshot();
        // Composite transparency over white before filling so erased pixels match the visible surface.
        const layer = document.createElement("canvas");
        layer.width = CANVAS_WIDTH;
        layer.height = CANVAS_HEIGHT;
        const layerContext = layer.getContext("2d")!;
        layerContext.fillStyle = "white";
        layerContext.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        layerContext.drawImage(canvas, 0, 0);
        const data = layerContext.getImageData(
          0,
          0,
          CANVAS_WIDTH,
          CANVAS_HEIGHT,
        ).data;
        busy = true;
        status();
        const fail = (message: string) => {
          if (!alive) return;
          busy = false;
          propsRef.current.onError?.(message);
          status();
          drain();
        };
        worker.onmessage = (
          event: MessageEvent<{
            data?: Uint8ClampedArray<ArrayBuffer>;
            changed?: boolean;
            error?: string;
          }>,
        ) => {
          if (!alive) return;
          if (event.data.error || !event.data.data) {
            fail(event.data.error || "Fill failed.");
            return;
          }
          if (event.data.changed) {
            context.putImageData(
              new ImageData(event.data.data, CANVAS_WIDTH, CANVAS_HEIGHT),
              0,
              0,
            );
            history.push(actionId, before);
            hasInk = detectInk();
            emit({
              ...base(actionId),
              type: "fill",
              point: p,
              color,
              tolerance: 0,
            });
          }
          busy = false;
          status();
          drain();
        };
        worker.onerror = () => {
          worker?.terminate();
          worker = undefined;
          fail("Fill worker failed.");
        };
        try {
          worker.postMessage(
            {
              data,
              width: CANVAS_WIDTH,
              height: CANVAS_HEIGHT,
              x: Math.floor(p.x),
              y: Math.floor(p.y),
              color,
            },
            [data.buffer],
          );
        } catch {
          worker?.terminate();
          worker = undefined;
          fail("Could not start fill.");
        }
      };
      const down = (e: PointerEvent) => {
        e.stopImmediatePropagation();
        if (!artist || busy || active || e.button !== 0) return;
        e.preventDefault();
        const started = performance.now();
        const p = point(e, started);
        const settings = { ...propsRef.current.settings };
        if (settings.tool === "fill") {
          fill(p, settings.color);
          return;
        }
        const actionId = uid(),
          before = snapshot(),
          ext = external(p);
        artist.mode = settings.tool === "eraser" ? "erase" : "draw";
        artist.color = settings.color;
        artist.weight = (settings.size * canvas.offsetWidth) / CANVAS_WIDTH;
        artist.adaptiveStroke = false;
        artist.pressureLow = 1;
        artist.pressureHigh = 1;
        artist.beginStroke(ext.x, ext.y);
        // Atrament strokes a quadratic path; a nonzero segment is needed for a visible tap.
        const next = artist.draw(ext.x + 0.1, ext.y, ext.x, ext.y, p.pressure);
        active = {
          pointerId: e.pointerId,
          actionId,
          before,
          last: p,
          previousX: next.x,
          previousY: next.y,
          started,
        };
        canvas.setPointerCapture(e.pointerId);
        emit({ ...base(actionId), type: "stroke.start", settings, point: p });
      };
      const move = (e: PointerEvent) => {
        e.stopImmediatePropagation();
        if (!active || !artist || e.pointerId !== active.pointerId) return;
        e.preventDefault();
        const points: CanvasPoint[] = [];
        const coalesced = e.getCoalescedEvents?.() || [];
        for (const sample of coalesced.length ? coalesced : [e]) {
          const p = point(sample, active.started),
            ext = external(p);
          const next = artist.draw(
            ext.x,
            ext.y,
            active.previousX,
            active.previousY,
            p.pressure,
          );
          active.previousX = next.x;
          active.previousY = next.y;
          active.last = p;
          points.push(p);
        }
        if (points.length)
          emit({ ...base(active.actionId), type: "stroke.append", points });
      };
      const up = (e: PointerEvent) => {
        e.stopImmediatePropagation();
        if (active?.pointerId === e.pointerId) {
          const p = point(e, active.started);
          if (artist && (p.x !== active.last.x || p.y !== active.last.y)) {
            const ext = external(p);
            artist.draw(
              ext.x,
              ext.y,
              active.previousX,
              active.previousY,
              p.pressure,
            );
            emit({
              ...base(active.actionId),
              type: "stroke.append",
              points: [p],
            });
          }
          active.last = p;
          finish();
        }
      };
      const cancel = (e: PointerEvent) => {
        e.stopImmediatePropagation();
        if (active?.pointerId === e.pointerId) finish();
      };
      const hidden = () => {
        if (document.hidden) finish();
      };
      const engine: Engine = {
        finish,
        undo: () =>
          command(() => {
            const entry = history.undo(snapshot());
            if (!entry) return;
            restore(entry.snapshot);
            const actionId = uid();
            emit({
              ...base(actionId),
              type: "history.undo",
              targetActionId: entry.actionId,
            });
            status();
          }),
        redo: () =>
          command(() => {
            const entry = history.redo(snapshot());
            if (!entry) return;
            restore(entry.snapshot);
            const actionId = uid();
            emit({
              ...base(actionId),
              type: "history.redo",
              targetActionId: entry.actionId,
            });
            status();
          }),
        clear: () =>
          command(() => {
            const before = snapshot();
            context.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
            hasInk = false;
            const actionId = uid();
            history.push(actionId, before);
            emit({ ...base(actionId), type: "canvas.clear" });
            status();
          }),
      };
      engineRef.current = engine;
      canvas.addEventListener("pointerdown", down, true);
      canvas.addEventListener("pointermove", move, true);
      canvas.addEventListener("pointerup", up, true);
      canvas.addEventListener("pointercancel", cancel, true);
      canvas.addEventListener("lostpointercapture", cancel, true);
      document.addEventListener("visibilitychange", hidden);
      try {
        worker = new Worker(new URL("./fill.worker.ts", import.meta.url));
      } catch {
        propsRef.current.onError?.("Fill worker is unavailable.");
      }
      import("atrament")
        .then(({ default: Constructor }) => {
          if (!alive) return;
          artist = new Constructor(canvas, {
            width: CANVAS_WIDTH,
            height: CANVAS_HEIGHT,
          });
          status();
        })
        .catch(() =>
          propsRef.current.onError?.("Could not initialize drawing canvas."),
        );
      status();
      return () => {
        finish();
        alive = false;
        engineRef.current = null;
        queue = [];
        worker?.terminate();
        canvas.removeEventListener("pointerdown", down, true);
        canvas.removeEventListener("pointermove", move, true);
        canvas.removeEventListener("pointerup", up, true);
        canvas.removeEventListener("pointercancel", cancel, true);
        canvas.removeEventListener("lostpointercapture", cancel, true);
        document.removeEventListener("visibilitychange", hidden);
        artist?.destroy();
      };
    }, []);
    useEffect(() => {
      engineRef.current?.finish();
    }, [props.settings.tool, props.settings.color, props.settings.size]);
    return (
      <canvas
        ref={canvasRef}
        width={CANVAS_WIDTH}
        height={CANVAS_HEIGHT}
        className={[styles.surface, props.className].filter(Boolean).join(" ")}
        aria-label="Drawing canvas"
        aria-busy="true"
        data-ready="false"
        data-testid="drawing-canvas"
      />
    );
  },
);
export default DrawingCanvas;
