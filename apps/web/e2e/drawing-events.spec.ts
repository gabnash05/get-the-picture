import { expect, test } from "@playwright/test";
import type { DrawingBatch } from "../src/contracts/drawing";

test("batches a held stroke, flushes its tail, and stays silent while idle", async ({
  browser,
}) => {
  const context = await browser.newContext();
  try {
    await context.addInitScript(() =>
      localStorage.setItem(
        "mtmai.player.v1",
        JSON.stringify({
          name: "Zork",
          avatar: { shape: "pebble", expression: "smile", color: "cyan" },
        }),
      ),
    );
    const page = await context.newPage();
    const batches: DrawingBatch[] = [];
    const pending: Promise<void>[] = [];
    page.on("console", (message) => {
      if (
        message.type() !== "info" ||
        !message.text().startsWith("[drawing:batch]")
      )
        return;
      pending.push(
        message
          .args()[1]
          .jsonValue()
          .then((value) => {
            batches.push(value as DrawingBatch);
          }),
      );
    });
    await page.goto("/room/?code=EVENTS");
    const canvas = page.locator("canvas[aria-label='Drawing canvas']");
    await expect(canvas).toBeVisible();
    const box = await canvas.boundingBox();
    expect(box).not.toBeNull();
    await page.waitForTimeout(500);
    expect(batches).toHaveLength(0);
    await page.mouse.move(box!.x + 30, box!.y + 30);
    await page.mouse.down();
    for (let i = 1; i <= 8; i++) {
      await page.mouse.move(box!.x + 30 + i * 10, box!.y + 30 + i * 5);
      await page.waitForTimeout(25);
    }
    await expect.poll(() => batches.length).toBeGreaterThan(0);
    expect(batches.some((batch) => batch.flushReason === "interval")).toBe(
      true,
    );
    await page.mouse.up();
    await expect
      .poll(() => batches.some((batch) => batch.flushReason === "stroke-end"))
      .toBe(true);
    await Promise.all(pending);
    let expectedSeq = 1;
    for (const batch of batches) {
      expect(batch.clientSeq[0]).toBe(expectedSeq);
      expect(batch.operationCount).toBe(batch.operations.length);
      expect(batch.clientSeq[1]).toBe(expectedSeq + batch.operationCount - 1);
      expect(batch.operations.map((op) => op.clientSeq)).toEqual(
        Array.from({ length: batch.operationCount }, (_, i) => expectedSeq + i),
      );
      expect(batch.byteCount).toBe(
        Buffer.byteLength(JSON.stringify(batch), "utf8"),
      );
      expect(batch.pointCount).toBe(
        batch.operations.reduce(
          (n, op) =>
            n +
            (op.type === "stroke.append"
              ? op.points.length
              : op.type === "stroke.start" ||
                  op.type === "stroke.end" ||
                  op.type === "fill"
                ? 1
                : 0),
          0,
        ),
      );
      expectedSeq = batch.clientSeq[1] + 1;
    }
    const count = batches.length;
    await page.waitForTimeout(150);
    expect(batches).toHaveLength(count);
  } finally {
    await context.close();
  }
});
