"use client";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  CRAYON_COLORS,
  type PlayerProfile,
  type AvatarConfig,
} from "../../contracts/player";
import {
  DEFAULT_DRAWING_SETTINGS,
  type CanvasOperation,
  type CanvasStatus,
  type DrawingBatcher,
  type DrawingCanvasHandle,
  type DrawingTool,
} from "../../contracts/drawing";
import DrawingCanvas from "../canvas/DrawingCanvas";
import { createDrawingBatcher } from "../drawing-events";
import { Avatar } from "../player/Avatar";
import { readPlayerProfile } from "../player/profile";
import "./room.css";

const sample: Record<string, AvatarConfig> = {
  Mina: { shape: "droplet", expression: "smile", color: "green" },
  Jo: { shape: "pebble", expression: "wow", color: "pink" },
  Ken: { shape: "spark", expression: "wink", color: "orange" },
};
const initialStatus: CanvasStatus = {
  canUndo: false,
  canRedo: false,
  busy: false,
  hasInk: false,
};
type ChatMessage = { name: string; text: string };
function Person({
  name,
  avatar,
  note,
}: {
  name: string;
  avatar: AvatarConfig;
  note: string;
}) {
  return (
    <div className="room-person">
      <Avatar avatar={avatar} />
      <span>
        <strong>{name}</strong>
        <small>{note}</small>
      </span>
    </div>
  );
}
export default function RoomScreen() {
  const router = useRouter();
  const search = useSearchParams();
  const roomCode = search.get("code")?.trim() ?? "";
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [settings, setSettings] = useState(DEFAULT_DRAWING_SETTINGS);
  const [status, setStatus] = useState(initialStatus);
  const [error, setError] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [copied, setCopied] = useState(false);
  const canvas = useRef<DrawingCanvasHandle>(null);
  const batcher = useRef<DrawingBatcher | null>(null);
  useEffect(() => {
    const saved = readPlayerProfile();
    if (!roomCode || !saved) {
      router.replace(roomCode ? `/?code=${encodeURIComponent(roomCode)}` : "/");
      return;
    }
    // The static page cannot access browser storage until hydration.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setProfile(saved);
  }, [roomCode, router]);
  useEffect(() => {
    if (!roomCode) return;
    const next = createDrawingBatcher({ roomCode, canvasId: "local-canvas" });
    batcher.current = next;
    return () => {
      queueMicrotask(() => {
        if (batcher.current === next) batcher.current = null;
        next.dispose();
      });
    };
  }, [roomCode]);
  const onOperation = useCallback((operation: CanvasOperation) => {
    setError(false);
    batcher.current?.enqueue(operation);
  }, []);
  const onError = useCallback((detail: string) => {
    console.error("Drawing canvas error:", detail);
    setError(true);
  }, []);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (
        target?.isContentEditable ||
        target?.closest("input, textarea, select, [contenteditable=true]")
      )
        return;
      const key = event.key.toLowerCase();
      if (
        (event.ctrlKey || event.metaKey) &&
        !event.altKey &&
        (key === "z" || key === "y")
      ) {
        event.preventDefault();
        if (status.busy) return;
        if (key === "y" || event.shiftKey) {
          if (status.canRedo) canvas.current?.redo();
        } else if (status.canUndo) canvas.current?.undo();
        return;
      }
      if (
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey &&
        ["b", "e", "f"].includes(key)
      )
        setSettings((current) => ({
          ...current,
          tool: (
            { b: "brush", e: "eraser", f: "fill" } as Record<
              string,
              DrawingTool
            >
          )[key],
        }));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [status]);
  function addMessage(event: FormEvent) {
    event.preventDefault();
    const text = message.trim();
    if (!text || !profile) return;
    setMessages((current) => [...current, { name: profile.name, text }]);
    setMessage("");
  }
  async function copyCode() {
    try {
      await navigator.clipboard.writeText(roomCode);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }
  if (!profile || !roomCode) return null;
  return (
    <main className="room-screen">
      <header className="room-header">
        <div className="room-brand">
          <img src="/design/assets/more-than-meets-the-ai-icon.png" alt="" />
          <strong>
            More Than
            <br />
            Meets the AI
          </strong>
        </div>
        <div className="room-code">
          <span>
            Room <strong>{roomCode}</strong>
          </span>
          <button type="button" onClick={copyCode}>
            {copied ? "Copied!" : "Copy code"}
          </button>
        </div>
        <div className="room-current">
          <Avatar avatar={profile.avatar} />
          <strong>{profile.name}</strong>
          <button
            className="room-button"
            type="button"
            onClick={() => router.push("/")}
            aria-label="Leave room"
          >
            ↪
          </button>
        </div>
      </header>
      <div className="room-layout">
        <aside className="room-teams" aria-label="Team rosters">
          <section className="room-team">
            <h2>
              Team Cyan <span>0 pts</span>
            </h2>
            <div className="room-people">
              <Person
                name={profile.name}
                avatar={profile.avatar}
                note="You · drawing"
              />
              <Person name="Mina" avatar={sample.Mina} note="Guessing" />
            </div>
            <p>Your team</p>
          </section>
          <section className="room-team room-team-pink">
            <h2>
              Team Pink <span>0 pts</span>
            </h2>
            <div className="room-people">
              <Person name="Jo" avatar={sample.Jo} note="Drawing" />
              <Person name="Ken" avatar={sample.Ken} note="Guessing" />
            </div>
            <p>Still guessing</p>
          </section>
        </aside>
        <section className="room-drawing" aria-label="Drawing area">
          <div className="room-prompt">
            <div>
              <span className="room-eyebrow">You are drawing</span>
              <strong>Banana</strong>
              <span>Teammates see _ _ _ _ _ _</span>
            </div>
            <div className="room-time">
              <span>Time</span>
              <strong>--:--</strong>
            </div>
          </div>
          <div className="room-board">
            <DrawingCanvas
              ref={canvas}
              settings={settings}
              onOperation={onOperation}
              onStatusChange={setStatus}
              onError={onError}
            />
          </div>
          {error && (
            <div className="room-error" role="alert">
              <span>
                Something went wrong with the canvas. Please try again.
              </span>
              <button
                className="room-button"
                type="button"
                onClick={() => setError(false)}
              >
                Dismiss
              </button>
            </div>
          )}
          <div className="room-tools">
            <div className="room-tool-row">
              <div className="room-tool-group">
                {(
                  [
                    ["brush", "✎", "Brush"],
                    ["eraser", "▱", "Eraser"],
                    ["fill", "◩", "Fill"],
                  ] as const
                ).map(([tool, icon, label]) => (
                  <button
                    className="room-button"
                    key={tool}
                    type="button"
                    aria-pressed={settings.tool === tool}
                    onClick={() =>
                      setSettings((current) => ({ ...current, tool }))
                    }
                  >
                    <span aria-hidden="true">{icon}</span> {label}
                  </button>
                ))}
              </div>
              <div className="room-tool-group">
                <button
                  className="room-button"
                  type="button"
                  disabled={!status.canUndo || status.busy}
                  onClick={() => canvas.current?.undo()}
                >
                  ↶ Undo
                </button>
                <button
                  className="room-button"
                  type="button"
                  disabled={!status.canRedo || status.busy}
                  onClick={() => canvas.current?.redo()}
                >
                  ↷ Redo
                </button>
                <button
                  className="room-button"
                  type="button"
                  disabled={!status.hasInk || status.busy}
                  onClick={() => canvas.current?.clear()}
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="room-tool-row">
              <div className="room-palette" aria-label="Drawing colors">
                {["#181321", ...Object.values(CRAYON_COLORS), "#FFFFFF"].map(
                  (color) => (
                    <button
                      key={color}
                      type="button"
                      aria-label={`Color ${color}`}
                      aria-pressed={settings.color.toUpperCase() === color}
                      style={{ background: color }}
                      onClick={() =>
                        setSettings((current) => ({ ...current, color }))
                      }
                    />
                  ),
                )}
                <label className="room-custom" title="Custom color">
                  <span className="room-sr">Custom color</span>
                  <input
                    type="color"
                    value={settings.color}
                    onChange={(event) =>
                      setSettings((current) => ({
                        ...current,
                        color: event.target.value,
                      }))
                    }
                  />
                </label>
              </div>
              <label className="room-size">
                Size{" "}
                <input
                  type="range"
                  disabled={settings.tool === "fill"}
                  min="2"
                  max="40"
                  value={settings.size}
                  onChange={(event) =>
                    setSettings((current) => ({
                      ...current,
                      size: Number(event.target.value),
                    }))
                  }
                />
                <output>{settings.size}</output>
              </label>
            </div>
          </div>
        </section>
        <aside className="room-chat-column">
          <section className="room-chat">
            <h2>Team chat</h2>
            <div className="room-messages" aria-live="polite">
              {messages.length === 0 ? (
                <p>Say hello to your team!</p>
              ) : (
                messages.map((entry, index) => (
                  <p key={index}>
                    <strong>{entry.name}: </strong>
                    {entry.text}
                  </p>
                ))
              )}
            </div>
            <form onSubmit={addMessage}>
              <label className="room-sr" htmlFor="room-message">
                Message your team
              </label>
              <input
                id="room-message"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Say something..."
                maxLength={300}
              />
              <button className="room-button" type="submit">
                Send
              </button>
            </form>
          </section>
          <section className="room-ai">
            <strong>✦ AI guesser</strong>
            <p>Waiting for a drawing.</p>
          </section>
        </aside>
      </div>
    </main>
  );
}
