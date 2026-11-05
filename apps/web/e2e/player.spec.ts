import { test, expect } from "@playwright/test";

test("customization, creation and profile survive refresh", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Your name").fill("  Alex  ");
  await page.getByRole("button", { name: "Spark", exact: true }).click();
  await page.getByRole("button", { name: "Wink", exact: true }).click();
  await page.getByRole("button", { name: "Purple character" }).click();
  await page.getByRole("button", { name: /Create a room/ }).click();
  await expect(page).toHaveURL(/\/room\/\?code=[A-Z2-9]{6}$/);
  await expect(page.getByText("You · drawing")).toBeVisible();
  expect(
    await page.evaluate(() =>
      JSON.parse(localStorage.getItem("mtmai.player.v1")!),
    ),
  ).toEqual({
    name: "Alex",
    avatar: { shape: "spark", expression: "wink", color: "purple" },
  });
  await page.reload();
  await expect(page.getByText("You · drawing")).toBeVisible();
  await page.getByRole("button", { name: "Leave room" }).click();
  await expect(page.getByLabel("Your name")).toHaveValue("Alex");
  await expect(
    page.getByRole("button", { name: "Spark", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("button", { name: "Wink", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("button", { name: "Purple character" }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("direct room link retains its code through guest join", async ({
  page,
}) => {
  await page.goto("/room/?code=hello%20world");
  await expect(page).toHaveURL(/\/?\?code=hello%20world$/);
  await expect(page.getByLabel("Already got a code?")).toHaveValue(
    "hello world",
  );
  await page.getByLabel("Your name").fill("Sam");
  await page.getByRole("button", { name: "Join room" }).click();
  await expect(page).toHaveURL(/\/room\/\?code=hello%20world$/);
  await expect(page.getByText("hello world", { exact: true })).toBeVisible();
});

test("reduced motion stops artwork animations", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const wrappers = page.locator(".player-bob");
  await expect(wrappers).toHaveCount(4);
  for (const wrapper of await wrappers.all())
    await expect(wrapper).toHaveCSS("animation-name", "none");
});
