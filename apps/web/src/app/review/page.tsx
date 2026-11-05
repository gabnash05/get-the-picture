"use client";
import { useRouter } from "next/navigation";
import { saveRoomSession } from "@/features/room-client";
import { seedReviewScenario } from "@/features/room-client/review";

const scenarios = [
  ["lobby", "Lobby · host"],
  ["drawer", "Drawing · drawer"],
  ["guesser", "Drawing · guesser"],
  ["result-correct", "Result · correct"],
  ["result-missed", "Result · missed"],
  ["restoring", "Restoring"],
  ["drawer-away", "Drawer disconnected"],
  ["ai-guessing", "AI · guessing"],
  ["ai-wrong", "AI · wrong"],
  ["ai-correct", "AI · correct"],
  ["team-minimum", "Team minimum blocker"],
  ["host-recovery", "Host recovery"],
  ["host-transfer", "Host transfer"],
  ["invite-full", "Invitation · full"],
  ["invite-not-found", "Invitation · not found"],
  ["invite-in-progress", "Invitation · in progress"],
] as const;
export default function ReviewPage() {
  const router = useRouter();
  return (
    <main
      style={{
        padding: "2rem",
        display: "grid",
        gap: "1rem",
        justifyItems: "start",
      }}
    >
      <h1>Local room review</h1>
      <p>These controls seed simulated room states for review.</p>
      {scenarios.map(([scenario, label]) => (
        <button
          className="room-button"
          key={scenario}
          onClick={async () => {
            const session = await seedReviewScenario(scenario);
            if (scenario.startsWith("invite-")) {
              router.push(`/?code=${encodeURIComponent(session.snapshot.code)}`);
            } else {
              saveRoomSession(session);
              router.push(`/room/?code=${encodeURIComponent(session.snapshot.code)}`);
            }
          }}
        >
          {label}
        </button>
      ))}
    </main>
  );
}
