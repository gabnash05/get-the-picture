import { Suspense } from "react";
import RoomScreen from "@/features/room/RoomScreen";
export default function RoomPage() {
  return (
    <Suspense
      fallback={
        <main className="page-loading">
          <h1>Getting your room ready...</h1>
        </main>
      }
    >
      <RoomScreen />
    </Suspense>
  );
}
