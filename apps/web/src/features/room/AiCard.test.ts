import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import type { RoomGame } from "@/contracts/room";
import { AiCard } from "./AiCard";
import styles from "./AiCard.module.css";

it("keeps an unavailable legacy result from looking solved", () => {
  const game = { aiStatus: "correct", result: { aiCorrect: true, aiAnswers: ["cat"], word: "cat", deltas: {} } } as unknown as RoomGame;
  const html = renderToStaticMarkup(createElement(AiCard, { game, result: true, unavailable: true }));
  expect(html).toContain("AI unavailable");
  expect(html).not.toContain(styles.solved);
  expect(html).not.toContain("Guessed it");
});
