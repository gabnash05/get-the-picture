import { test, expect } from "@playwright/test";
const viewports = [
  [360, 800],
  [390, 844],
  [430, 932],
  [600, 960],
  [820, 1180],
  [1024, 768],
  [1366, 768],
  [1440, 900],
  [1920, 1080],
] as const;
for (const [width, height] of viewports) {
  test(`login and room fit ${width}x${height}`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.addInitScript(() =>
      localStorage.setItem(
        "mtmai.player.v1",
        JSON.stringify({
          name: "Zork",
          avatar: { shape: "pebble", expression: "smile", color: "cyan" },
        }),
      ),
    );
    for (const path of ["/", "/room/?code=VIEWPORT"]) {
      await page.goto(path);
      if (path === "/")
        await expect(page.getByLabel("Your name")).toBeVisible();
      else await expect(page.getByLabel("Drawing canvas")).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      const layout = await page.evaluate(() => ({
        width: innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        fonts:
          document.fonts.check("600 24px Fredoka") &&
          document.fonts.check("400 16px Nunito"),
        overflow: [...document.querySelectorAll<HTMLElement>("main *")]
          .filter(
            (element) =>
              element.getClientRects().length &&
              !element.closest("svg") &&
              getComputedStyle(element).clip === "auto" &&
              getComputedStyle(element).overflowX !== "auto" &&
              getComputedStyle(element).overflowX !== "scroll" &&
              element.scrollWidth > element.clientWidth + 3,
          )
          .map((element) => ({
            tag: element.tagName,
            className: element.className,
            width: element.clientWidth,
            scroll: element.scrollWidth,
          })),
      }));
      expect(layout.scrollWidth, `${path}: page overflow`).toBeLessThanOrEqual(
        width,
      );
      expect(layout.overflow, `${path}: clipped nested content`).toEqual([]);
      expect(layout.fonts).toBe(true);
      if (path !== "/" && width >= 1100) {
        const toolbar = await page.locator(".room-tools").boundingBox();
        expect(
          toolbar!.y + toolbar!.height,
          "canvas tools should fit with the canvas",
        ).toBeLessThanOrEqual(height);
      }
    }
  });
}
