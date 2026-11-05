export type Snapshot = { image: ImageData; hasInk: boolean };
type Entry = { actionId: string; snapshot: Snapshot };

/** Stores at most 20 full-size bitmap snapshots across both branches. */
export class BitmapHistory {
  private past: Entry[] = [];
  private future: Entry[] = [];
  constructor(
    private limit = 20,
    private byteLimit = 64 * 1024 * 1024,
  ) {}
  get canUndo() {
    return this.past.length > 0;
  }
  get canRedo() {
    return this.future.length > 0;
  }
  push(actionId: string, snapshot: Snapshot) {
    this.future = [];
    this.past.push({ actionId, snapshot });
    while (this.past.length > this.limit || this.bytes() > this.byteLimit)
      this.past.shift();
  }
  undo(current: Snapshot) {
    const entry = this.past.pop();
    if (!entry) return undefined;
    this.future.push({ actionId: entry.actionId, snapshot: current });
    return entry;
  }
  redo(current: Snapshot) {
    const entry = this.future.pop();
    if (!entry) return undefined;
    this.past.push({ actionId: entry.actionId, snapshot: current });
    return entry;
  }
  private bytes() {
    return [...this.past, ...this.future].reduce(
      (n, entry) => n + entry.snapshot.image.data.byteLength,
      0,
    );
  }
}
