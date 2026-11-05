export const CANVAS_WIDTH = 1024;
export const CANVAS_HEIGHT = 768;
export type DrawingTool = "brush" | "eraser" | "fill";
export interface DrawingSettings {
  tool: DrawingTool;
  color: string;
  size: number;
}
export const DEFAULT_DRAWING_SETTINGS: DrawingSettings = {
  tool: "brush",
  color: "#181321",
  size: 12,
};
export interface CanvasPoint {
  x: number;
  y: number;
  time: number;
  pressure?: number;
}
export interface OperationBase {
  opId: string;
  actionId: string;
  at: number;
}
export type CanvasOperation =
  | (OperationBase & {
      type: "stroke.start";
      settings: DrawingSettings;
      point: CanvasPoint;
    })
  | (OperationBase & { type: "stroke.append"; points: CanvasPoint[] })
  | (OperationBase & { type: "stroke.end"; point: CanvasPoint })
  | (OperationBase & {
      type: "fill";
      point: CanvasPoint;
      color: string;
      tolerance: number;
    })
  | (OperationBase & {
      type: "history.undo" | "history.redo";
      targetActionId: string;
    })
  | (OperationBase & { type: "canvas.clear" });
export interface CanvasStatus {
  canUndo: boolean;
  canRedo: boolean;
  busy: boolean;
  hasInk: boolean;
}
export interface DrawingCanvasHandle {
  undo(): void;
  redo(): void;
  clear(): void;
}
export interface DrawingCanvasProps {
  settings: DrawingSettings;
  onOperation(operation: CanvasOperation): void;
  onStatusChange?(status: CanvasStatus): void;
  onError?(message: string): void;
  className?: string;
}
export type FlushReason =
  "interval" | "stroke-end" | "command" | "manual" | "dispose";
export type SequencedOperation = CanvasOperation & { clientSeq: number };
export interface DrawingBatch {
  transport: "console";
  batchId: string;
  roomCode: string;
  canvasId: string;
  clientSeq: [number, number];
  flushReason: FlushReason;
  targetIntervalMs: number;
  elapsedMs: number;
  operationCount: number;
  pointCount: number;
  byteCount: number;
  operations: SequencedOperation[];
}
export interface DrawingBatcherOptions {
  roomCode: string;
  canvasId: string;
  intervalMs?: number;
  send?(batch: DrawingBatch): void;
  now?(): number;
}
export interface DrawingBatcher {
  enqueue(operation: CanvasOperation): void;
  flush(reason?: FlushReason): void;
  dispose(): void;
}
