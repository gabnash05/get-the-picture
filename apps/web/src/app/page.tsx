import { Suspense } from "react";
import LoginScreen from "@/features/player/LoginScreen";
export default function HomePage() {
  return (
    <Suspense
      fallback={
        <main className="page-loading">
          <h1>More Than Meets the AI</h1>
          <p>Getting your player ready...</p>
        </main>
      }
    >
      <LoginScreen />
    </Suspense>
  );
}
