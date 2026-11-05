import { expect, test, type Page } from "@playwright/test";

test.use({ hasTouch: true });

async function setup(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem(
      "mtmai.player.v1",
      JSON.stringify({
        name: "Canvas Tester",
        avatar: { shape: "pebble", expression: "smile", color: "cyan" },
      }),
    ),
  );
  await page.goto("/room/?code=CANVAS");
  const canvas = page.getByLabel("Drawing canvas");
  await expect(canvas).toHaveAttribute("data-ready", "true");
  return canvas;
}
async function position(page: Page, x: number, y: number) {
  const canvas = page.getByLabel("Drawing canvas");
  await canvas.scrollIntoViewIfNeeded();
  const box = (await canvas.boundingBox())!;
  return {
    x: box.x + (x * box.width) / 1024,
    y: box.y + (y * box.height) / 768,
  };
}
async function pixel(page: Page, x: number, y: number) {
  return page
    .getByLabel("Drawing canvas")
    .evaluate(
      (element: HTMLCanvasElement, coords) =>
        Array.from(
          element.getContext("2d")!.getImageData(coords.x, coords.y, 1, 1).data,
        ),
      { x, y },
    );
}
async function clickAt(page: Page, x: number, y: number) {
  const p = await position(page, x, y);
  await page.mouse.click(p.x, p.y);
}
async function line(page: Page, points: [number, number][]) {
  const first = await position(page, ...points[0]);
  await page.mouse.move(first.x, first.y);
  await page.mouse.down();
  for (const point of points.slice(1)) {
    const p = await position(page, ...point);
    await page.mouse.move(p.x, p.y, { steps: 12 });
  }
  await page.mouse.up();
}
const ink = (rgba: number[]) =>
  rgba[3] > 0 && rgba.slice(0, 3).some((c) => c < 220);

test("brush, size, eraser, undo and resize preserve pixels", async ({
  page,
}) => {
  await setup(page);
  await page.getByRole("button", { name: "Color #FF4343" }).click();
  await page.getByLabel("Size").fill("40");
  await clickAt(page, 200, 200);
  expect((await pixel(page, 200, 200)).slice(0, 3)).toEqual([255, 67, 67]);
  expect(ink(await pixel(page, 210, 200))).toBe(true);
  await line(page, [
    [300, 300],
    [450, 300],
  ]);
  expect(ink(await pixel(page, 360, 300))).toBe(true);
  await page.setViewportSize({ width: 900, height: 700 });
  expect(ink(await pixel(page, 360, 300))).toBe(true);
  await page.getByRole("button", { name: "Eraser" }).click();
  await clickAt(page, 360, 300);
  expect((await pixel(page, 360, 300))[3]).toBe(0);
  await page.getByRole("button", { name: /Undo/ }).click();
  expect(ink(await pixel(page, 360, 300))).toBe(true);
});

test("worker fill respects boundaries and history, clear, and new branches", async ({
  page,
}) => {
  const canvas = await setup(page);
  await page.getByLabel("Size").fill("40");
  await line(page, [
    [300, 200],
    [700, 200],
    [700, 550],
    [300, 550],
    [300, 200],
    [400, 200],
  ]);
  await page.getByRole("button", { name: "Color #FF4343" }).click();
  await page.getByRole("button", { name: "Fill" }).click();
  await clickAt(page, 500, 350);
  await expect(canvas).toHaveAttribute("aria-busy", "false");
  await expect
    .poll(async () => (await pixel(page, 500, 350)).slice(0, 3))
    .toEqual([255, 67, 67]);
  expect(ink(await pixel(page, 100, 100))).toBe(false);
  await page.getByRole("button", { name: /Undo/ }).click();
  expect(ink(await pixel(page, 500, 350))).toBe(false);
  await page.getByRole("button", { name: /Redo/ }).click();
  expect((await pixel(page, 500, 350)).slice(0, 3)).toEqual([255, 67, 67]);
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  expect(ink(await pixel(page, 500, 350))).toBe(false);
  await page.getByRole("button", { name: /Undo/ }).click();
  expect((await pixel(page, 500, 350)).slice(0, 3)).toEqual([255, 67, 67]);
  await page.getByRole("button", { name: "Brush" }).click();
  await clickAt(page, 100, 100);
  await expect(page.getByRole("button", { name: /Redo/ })).toBeDisabled();
});

test("touch fill without prior move and pointer cancellation", async ({
  page,
}) => {
  const canvas = await setup(page);
  await page.getByRole("button", { name: "Color #3455FF" }).click();
  await page.getByRole("button", { name: "Fill" }).click();
  const p = await position(page, 500, 350);
  await page.touchscreen.tap(p.x, p.y);
  await expect
    .poll(async () => (await pixel(page, 500, 350)).slice(0, 3))
    .toEqual([52, 85, 255]);
  await page.getByRole("button", { name: "Brush" }).click();
  const start = await position(page, 200, 200);
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  await canvas.evaluate((el) =>
    el.dispatchEvent(
      new PointerEvent("pointercancel", {
        bubbles: true,
        pointerId: 1,
        pointerType: "mouse",
      }),
    ),
  );
  await page.mouse.up();
  await expect(page.getByRole("button", { name: /Undo/ })).toBeEnabled();
});
