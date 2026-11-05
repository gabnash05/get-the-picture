import type { RoomGame } from "@/contracts/room";

export function AiCard({ game, result }: { game?: RoomGame; result: boolean }) {
  return (
            <section className={`room-ai ai-${game?.aiStatus ?? "waiting"}`}>
              <h2>Your AI Rival</h2>
              {result && game?.result ? (
                <div className="ai-result">
                  <div className="ai-final">
                    <b>Final</b>{" "}
                    <strong>
                      {game.result.finalAnswer ??
                        game.result.aiAnswers.at(-1) ??
                        "—"}
                    </strong>{" "}
                    {game.result.aiCorrect ? "✓ Correct" : "× Miss"}
                  </div>
                  <span>Earlier guesses</span>
                  <ol>
                    {game.result.aiAnswers.slice(0, -1).map((a, i) => (
                      <li key={`${i}-${a}`}>{a}</li>
                    ))}
                  </ol>
                </div>
              ) : (
                <div className="ai-live">
                  <span className="ai-dots">● ● ●</span>
                  <p>
                    {game?.aiStatus === "correct"
                      ? "AI recognized it"
                      : game?.aiStatus === "wrong"
                        ? "AI missed"
                        : game?.aiStatus === "guessing"
                          ? "AI is guessing"
                          : "Waiting for a drawing"}
                  </p>
                </div>
              )}
            </section>
  );
}
