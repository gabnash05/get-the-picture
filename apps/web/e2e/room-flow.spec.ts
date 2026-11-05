import { expect, test } from "@playwright/test";

test("host lobby exposes defaults, blockers, and invite dialog", async ({ page }) => {
  await page.goto("/review/");
  await page.getByRole("button", { name: "Lobby · host" }).click();
  await expect(page.getByText("Everyone vs AI")).toBeVisible();
  await expect(page.getByRole("combobox", { name: "Mode" })).toContainText("Individual");
  await page.getByRole("button", { name: /Room REVIEW/ }).click();
  await expect(page.getByRole("dialog")).toContainText("Invite your crew");
  await expect(page.getByRole("button", { name: "Copy link" })).toBeVisible();
  await page.getByRole("button", { name: "Done" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("team minimum and supplied individual result are visible", async ({ page }) => {
  await page.goto("/review/");
  await page.getByRole("button", { name: "Team minimum blocker" }).click();
  await expect(page.getByText("Team 2 needs two connected players.")).toBeVisible();
  await expect(page.getByRole("button", { name: /Start match/ })).toBeDisabled();
  await page.goto("/review/");
  await page.getByRole("button", { name: "Result · correct" }).click();
  await expect(page.getByText("You got it!")).toBeVisible();
  await expect(page.getByText("Your round: 100 points")).toBeVisible();
  await expect(page.getByText("Final", { exact: true })).toBeVisible();
});
