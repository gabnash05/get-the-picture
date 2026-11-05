import { describe, expect, it } from "vitest";
import { BitmapHistory, type Snapshot } from "./history";
const snap = (n: number): Snapshot => ({
  image: { data: new Uint8ClampedArray([n, 0, 0, 0]) } as ImageData,
  hasInk: n > 0,
});
describe("bitmap history", () => {
  it("undoes and redoes action snapshots in order", () => {
    const h = new BitmapHistory();
    h.push("a", snap(0));
    h.push("b", snap(1));
    expect(h.undo(snap(2))?.actionId).toBe("b");
    expect(h.undo(snap(1))?.actionId).toBe("a");
    expect(h.redo(snap(0))?.snapshot.image.data[0]).toBe(1);
    expect(h.redo(snap(1))?.snapshot.image.data[0]).toBe(2);
    expect(h.canRedo).toBe(false);
  });
  it("discards redo after a new edit and evicts by count and bytes", () => {
    const h = new BitmapHistory(2, 8);
    h.push("a", snap(0));
    h.push("b", snap(1));
    h.push("c", snap(2));
    expect(h.undo(snap(3))?.actionId).toBe("c");
    h.push("d", snap(2));
    expect(h.canRedo).toBe(false);
    expect(h.undo(snap(4))?.actionId).toBe("d");
    expect(h.undo(snap(2))?.actionId).toBe("b");
    expect(h.canUndo).toBe(false);
    const small = new BitmapHistory(20, 4);
    small.push("a", snap(0));
    small.push("b", snap(1));
    expect(small.undo(snap(2))?.actionId).toBe("b");
    expect(small.canUndo).toBe(false);
  });
});
