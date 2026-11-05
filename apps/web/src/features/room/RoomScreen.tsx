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
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  createRoomClient,
  loadRoomSession,
  clearRoomSession,
} from "@/features/room-client";
import type { RoomClient, RoomSession, RoomSettings } from "@/contracts/room";
import { CRAYON_COLORS } from "@/contracts/player";
import {
  DEFAULT_DRAWING_SETTINGS,
  type CanvasStatus,
  type DrawingCanvasHandle,
  type DrawingBatcher,
} from "@/contracts/drawing";
import DrawingCanvas from "@/features/canvas/DrawingCanvas";
import { createDrawingBatcher } from "@/features/drawing-events";
import { Avatar } from "@/features/player/Avatar";
import { AiCard } from "./AiCard";
import "./room.css";

const emptyStatus: CanvasStatus = {
  canUndo: false,
  canRedo: false,
  busy: true,
  hasInk: false,
};
function Choice({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="room-setting">
      <span>{label}</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger aria-label={label}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}
const numbers = (from: number, to: number, suffix: string) =>
  Array.from({ length: to - from + 1 }, (_, i) => ({
    value: String(i + from),
    label: `${i + from} ${suffix}`,
  }));
export default function RoomScreen() {
  const router = useRouter(),
    search = useSearchParams(),
    code = search.get("code")?.trim().toUpperCase() ?? "";
  const [session, setSession] = useState<RoomSession | null>(null),
    [error, setError] = useState(""),
    [connection, setConnection] = useState("restoring"),
    [message, setMessage] = useState(""),
    [copyStatus, setCopyStatus] = useState(""),
    [settings, setSettings] = useState(DEFAULT_DRAWING_SETTINGS),
    [canvasStatus, setCanvasStatus] = useState(emptyStatus),
    [caughtUp, setCaughtUp] = useState(false);
  const client = useRef<RoomClient | null>(null),
    canvas = useRef<DrawingCanvasHandle>(null),
    batcher = useRef<DrawingBatcher | null>(null);
  const activeCanvas = useRef<{ id: string; generation: number } | null>(null);
  activeCanvas.current = session?.snapshot.game ? { id: session.snapshot.game.canvasId, generation: session.snapshot.game.generation } : null;
  useEffect(() => {
    const saved = loadRoomSession();
    if (!code || !saved || saved.code !== code) {
      router.replace(code ? `/?code=${encodeURIComponent(code)}` : "/");
      return;
    }
    const c = createRoomClient();
    client.current = c;
    let alive = true;
    const unsubscribe = c.subscribe((event) => {
      if (!alive) return;
      if (event.type === "snapshot")
        setSession((old) =>
          old
            ? {
                ...old,
                snapshot: event.snapshot,
                privateState: event.privateState,
              }
            : old,
        );
      if (event.type === "connection") {
        setConnection(event.status);
        if (event.status !== "connected") setCaughtUp(false);
      }
      if (event.type === "drawing") {
        if (activeCanvas.current?.id !== event.canvasId || activeCanvas.current.generation !== event.generation) return;
        setCaughtUp(false);
        const replay = event.reset
          ? canvas.current?.hydrate(event.operations)
          : canvas.current?.applyOperations(event.operations);
        void replay
          ?.then(() => {
            if (alive && event.caughtUp && activeCanvas.current?.id === event.canvasId && activeCanvas.current.generation === event.generation) setCaughtUp(true);
          })
          .catch(() =>
            setError("Could not restore the drawing. Please retry."),
          );
      }
    });
    c.resume(code, saved.resumeToken)
      .then((s) => {
        if (alive) {
          setSession(s);
          if (!s.snapshot.game) void c.resync().catch(e => setError(e instanceof Error ? e.message : "Could not restore this room."));
        }
      })
      .catch((e) => {
        if (alive) {
          setError(
            e instanceof Error ? e.message : "Could not restore this room.",
          );
          setConnection("disconnected");
        }
      });
    return () => {
      alive = false;
      unsubscribe();
      c.dispose();
      client.current = null;
    };
  }, [code, router]);
  const snap = session?.snapshot,
    game = snap?.game,
    me = snap?.players.find((p) => p.id === session?.playerId),
    host = snap?.hostId === session?.playerId,
    role = session?.privateState?.role,
    drawing = snap?.phase === "drawing",
    result = snap?.phase === "result";
  useEffect(() => {
    if (!code || !game?.canvasId) return;
    const b = createDrawingBatcher({
      roomCode: code,
      canvasId: game.canvasId,
      transport: "room-client",
      send: (batch) => {
        void client.current
          ?.submitDrawing(batch)
          .catch((e) => setError(e.message));
      },
    });
    batcher.current = b;
    return () => {
      b.dispose();
      batcher.current = null;
    };
  }, [code, game?.canvasId, game?.generation]);
  useEffect(() => {
    if (!game?.canvasId) return;
    void client.current
      ?.resync()
      .catch((e) =>
        setError(
          e instanceof Error ? e.message : "Could not restore the drawing.",
        ),
      );
  }, [game?.canvasId, game?.generation]);
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, [contenteditable=true]"))
        return;
      if (
        !drawing ||
        role !== "drawer" ||
        !caughtUp ||
        connection !== "connected" ||
        canvasStatus.busy
      )
        return;
      const key = event.key.toLowerCase();
      if (
        (event.ctrlKey || event.metaKey) &&
        !event.altKey &&
        (key === "z" || key === "y")
      ) {
        event.preventDefault();
        if (key === "y" || event.shiftKey) canvas.current?.redo();
        else canvas.current?.undo();
      } else if (
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey &&
        ["b", "e", "f"].includes(key)
      )
        setSettings((s) => ({
          ...s,
          tool: ({ b: "brush", e: "eraser", f: "fill" } as const)[
            key as "b" | "e" | "f"
          ],
        }));
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawing, role, caughtUp, connection, canvasStatus.busy]);
  const action = useCallback(async (fn: () => Promise<void>) => {
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Something went wrong. Please try again.",
      );
    }
  }, []);
  function send(event: FormEvent) {
    event.preventDefault();
    const text = message.trim();
    if (!text) return;
    void action(async () => {
      if (drawing && role === "guesser")
        await client.current?.submitGuess(text);
      else await client.current?.sendChat(text);
      setMessage("");
    });
  }
  function change(next: Partial<RoomSettings>) {
    if (!snap) return;
    void action(() =>
      client.current!.updateSettings({ ...snap.settings, ...next }),
    );
  }
  async function copy(value: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopyStatus("Copied!");
    } catch {
      setCopyStatus("Copy unavailable. Select the text and copy it manually.");
    }
  }
  if (!session || !snap || !me)
    return (
      <main className="room-loading">
        <h1>Getting your room ready…</h1>
        {error && (
          <p role="alert">
            {error}{" "}
            <button
              onClick={() => router.push(`/?code=${encodeURIComponent(code)}`)}
            >
              Return to entry
            </button>
          </p>
        )}
      </main>
    );
  const blockers =
    snap.startBlockers ??
    (snap.settings.mode === "individual"
      ? snap.players.filter((p) => p.connected).length < 2
        ? ["At least two connected players are needed."]
        : []
      : snap.teams
          .filter(
            (t) =>
              snap.players.filter((p) => p.connected && p.teamId === t.id)
                .length < 2,
          )
          .map((t) => `${t.name} needs at least two connected players.`));
  const link =
    typeof window !== "undefined"
      ? `${window.location.origin}/?code=${encodeURIComponent(code)}`
      : `/?code=${encodeURIComponent(code)}`;
  const roster = (teamId?: string) =>
    snap.players
      .filter((p) => snap.settings.mode === "individual" || p.teamId === teamId)
      .map((p) => (
        <div
          className={`room-person ${p.solved ? "is-solved" : ""}`}
          key={p.id}
        >
          <Avatar avatar={p.profile.avatar} />
          <span>
            <strong>
              {p.profile.name}
              {p.id === session.playerId ? " (you)" : ""}
            </strong>
            <small>
              {p.id === snap.hostId ? "Host · " : ""}
              {!p.connected
                ? "Disconnected"
                : p.solved
                  ? "Solved"
                  : game?.drawerId === p.id
                    ? "Drawing"
                    : "Connected"}
            </small>
          </span>
          {p.score !== undefined && <b>{p.score} pts</b>}
          {host && snap.phase === "lobby" && snap.settings.mode === "team" && (
            <Choice
              label={`Move ${p.profile.name}`}
              value={p.teamId ?? ""}
              options={snap.teams.map((t) => ({ value: t.id, label: t.name }))}
              onChange={(v) =>
                void action(() => client.current!.movePlayer(p.id, v))
              }
            />
          )}
        </div>
      ));
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
        <Dialog>
          <DialogTrigger asChild>
            <button className="room-code">
              Room <strong>{code}</strong> ↗
            </button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Invite your crew</DialogTitle>
            <DialogDescription>
              Share this code or link to invite someone.
            </DialogDescription>
            <label className="room-setting">
              Room code
              <input
                readOnly
                value={code}
                onFocus={(e) => e.currentTarget.select()}
              />
            </label>
            <button className="room-button" onClick={() => void copy(code)}>
              Copy code
            </button>
            <label className="room-setting">
              Room link
              <input
                readOnly
                value={link}
                onFocus={(e) => e.currentTarget.select()}
              />
            </label>
            <button className="room-button" onClick={() => void copy(link)}>
              Copy link
            </button>
            <p aria-live="polite">{copyStatus}</p>
            <DialogClose asChild>
              <button className="room-button">Done</button>
            </DialogClose>
          </DialogContent>
        </Dialog>
        <div className="room-current">
          <span className="room-demo">{session.demo ? "Local demo" : ""}</span>
          <Avatar avatar={me.profile.avatar} />
          <strong>{me.profile.name}</strong>
          <Dialog>
            <DialogTrigger asChild>
              <button className="room-button" aria-label="Leave room">
                ↪
              </button>
            </DialogTrigger>
            <DialogContent>
              <DialogTitle>Leave this room?</DialogTitle>
              <DialogDescription>
                Your seat will be released. If you are host, hosting transfers
                to another connected player; an empty room closes.
              </DialogDescription>
              <button
                className="room-button"
                onClick={() =>
                  void action(async () => {
                    await client.current!.leave();
                    clearRoomSession();
                    router.push("/");
                  })
                }
              >
                Leave room
              </button>
              <DialogClose asChild>
                <button className="room-button">Stay</button>
              </DialogClose>
            </DialogContent>
          </Dialog>
        </div>
      </header>
      {error && (
        <p className="room-error" role="alert">
          {error}
        </p>
      )}
      {!!snap.hostDisconnectedUntil && <p className="room-error" role="status">Host reconnecting. Hosting is reserved briefly before transfer.</p>}
      {drawing && game && !snap.players.find(p => p.id === game.drawerId)?.connected && <p className="room-error" role="status">The drawer disconnected. Their drawing remains visible.</p>}
      {(connection !== "connected" || (drawing && !caughtUp)) && (
        <p className="room-error" role="status">
          {connection === "restoring" || (drawing && !caughtUp)
            ? "Restoring your room and drawing…"
            : "Connection interrupted. Reconnect to continue."}{" "}
          {connection !== "connected" && (
            <button
              className="room-button"
              onClick={() => void action(() => client.current!.resync())}
            >
              Retry
            </button>
          )}
        </p>
      )}
      {snap.phase === "lobby" ? (
        <div className="lobby-layout">
          <section>
            <div className="lobby-heading">
              <div>
                <p className="room-eyebrow">YOUR PRIVATE ROOM</p>
                <h1>Get the crew together.</h1>
                <p>
                  Invite players, choose your settings, and get ready to draw.
                </p>
              </div>
            </div>
            <section className="room-panel">
              <h2>
                {snap.settings.mode === "individual"
                  ? "Everyone vs AI"
                  : "Players"}
              </h2>
              {snap.settings.mode === "individual"
                ? roster()
                : snap.teams.map((t) => (
                    <div className="room-team-block" key={t.id}>
                      <h3>{t.name}</h3>
                      {roster(t.id)}
                      {me.teamId !== t.id && (
                        <button
                          className="room-button"
                          onClick={() =>
                            void action(() => client.current!.selectTeam(t.id))
                          }
                        >
                          Join team
                        </button>
                      )}
                    </div>
                  ))}
            </section>
            <section className="room-panel room-chat">
              <h2>Room chat</h2>
              <div className="room-messages" aria-live="polite">
                {snap.chat.length ? (
                  snap.chat.map((m) => (
                    <p key={m.id}>
                      <strong>
                        {snap.players.find((p) => p.id === m.playerId)?.profile
                          .name ?? "Room"}
                        :{" "}
                      </strong>
                      {m.text}
                    </p>
                  ))
                ) : (
                  <p>Say hello to the room!</p>
                )}
              </div>
              <form onSubmit={send}>
                <input
                  aria-label="Message the room"
                  placeholder="Message the room…"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  maxLength={240}
                />
                <button className="room-button">Send</button>
              </form>
            </section>
          </section>
          <aside>
            <section className="room-panel room-settings">
              <h2>Room settings</h2>
              {host ? (
                <>
                  <Choice
                    label="Mode"
                    value={snap.settings.mode}
                    options={[
                      { value: "individual", label: "Individual" },
                      { value: "team", label: "Team" },
                    ]}
                    onChange={(v) =>
                      change({ mode: v as RoomSettings["mode"] })
                    }
                  />
                  {snap.settings.mode === "individual" ? (
                    <Choice
                      label="Player seats"
                      value={String(snap.settings.seats)}
                      options={numbers(2, 8, "seats")}
                      onChange={(v) => change({ seats: Number(v) })}
                    />
                  ) : (
                    <>
                      <Choice
                        label="Teams"
                        value={String(snap.settings.teamCount)}
                        options={numbers(2, 4, "teams")}
                        onChange={(v) => change({ teamCount: Number(v) })}
                      />
                      <Choice
                        label="Seats per team"
                        value={String(snap.settings.seatsPerTeam)}
                        options={numbers(2, 8, "seats")}
                        onChange={(v) => change({ seatsPerTeam: Number(v) })}
                      />
                    </>
                  )}
                  <Choice
                    label="Prompt rounds"
                    value={String(snap.settings.rounds)}
                    options={numbers(1, 20, "rounds")}
                    onChange={(v) => change({ rounds: Number(v) })}
                  />
                </>
              ) : (
                <p>
                  {snap.settings.mode === "individual"
                    ? `Individual · ${snap.settings.seats} seats`
                    : `Team · ${snap.settings.teamCount} teams · ${snap.settings.seatsPerTeam} seats per team`}
                  <br />
                  {snap.settings.rounds} prompt rounds
                </p>
              )}
              {blockers.map((b) => (
                <p className="room-blocker" key={b}>
                  {b}
                </p>
              ))}
              <button
                className="room-primary"
                disabled={
                  !host || blockers.length > 0 || connection !== "connected"
                }
                onClick={() => void action(() => client.current!.start())}
              >
                {host ? "Start match →" : `Waiting for ${snap.players.find(p => p.id === snap.hostId)?.profile.name ?? "host"}`}
              </button>
            </section>
            <section className="room-panel">
              <h2>How this room plays</h2>
              <p>
                {snap.settings.mode === "individual"
                  ? "Each guesser earns personal points. Solve before the AI for a stronger result; the drawer earns recognition and may earn a smaller AI bonus."
                  : "Work together for shared team points. Teams draw on separate canvases."}
              </p>
              <p>Drawers rotate each prompt round. No written answer clues.</p>
            </section>
          </aside>
        </div>
      ) : (
        <div className="room-layout">
          <aside className="room-teams">
            <section className="room-panel">
              <h2>
                {snap.settings.mode === "individual"
                  ? "Everyone vs AI"
                  : "Players"}
              </h2>
              {roster(me.teamId)}
            </section>
            {snap.settings.mode === "team" && snap.teams.filter(t => t.id !== me.teamId).map(t => <section className="room-panel" key={t.id}><h2>{t.name}</h2><p>{snap.players.some(p => p.teamId === t.id && p.solved) ? "Solved" : "Still guessing"}</p></section>)}
          </aside>
          <section className="room-drawing">
            <div className="room-prompt">
              <div>
                <span className="room-eyebrow">
                  {result
                    ? "Round complete"
                    : role === "drawer"
                      ? "You are drawing"
                      : "Guess the drawing"}
                </span>
                <strong>
                  {result
                    ? game?.result?.word
                    : role === "drawer"
                      ? session.privateState?.target
                      : game?.hint}
                </strong>
              </div>
              <div className="room-time">
                <span>Time</span>
                <strong>{game?.time ?? "--:--"}</strong>
              </div>
            </div>
            <div className="room-board">
              <DrawingCanvas
                ref={canvas}
                readOnly={
                  !drawing ||
                  role !== "drawer" ||
                  connection !== "connected" ||
                  !caughtUp
                }
                settings={settings}
                onOperation={(op) => batcher.current?.enqueue(op)}
                onStatusChange={setCanvasStatus}
                onError={setError}
              />
            </div>
            {drawing && role === "drawer" && (
              <fieldset
                className="room-tools"
                disabled={
                  !caughtUp || connection !== "connected" || canvasStatus.busy
                }
              >
                <div className="room-tool-row">
                  {(["brush", "eraser", "fill"] as const).map((tool) => (
                    <button
                      key={tool}
                      className="room-button"
                      aria-pressed={settings.tool === tool}
                      onClick={() => setSettings((s) => ({ ...s, tool }))}
                    >
                      {tool}
                    </button>
                  ))}
                  <button
                    className="room-button"
                    disabled={!canvasStatus.canUndo}
                    onClick={() => canvas.current?.undo()}
                  >
                    Undo
                  </button>
                  <button
                    className="room-button"
                    disabled={!canvasStatus.canRedo}
                    onClick={() => canvas.current?.redo()}
                  >
                    Redo
                  </button>
                  <button
                    className="room-button"
                    disabled={!canvasStatus.hasInk}
                    onClick={() => canvas.current?.clear()}
                  >
                    Clear
                  </button>
                </div>
                <div className="room-tool-row room-palette">
                  {["#181321", ...Object.values(CRAYON_COLORS), "#FFFFFF"].map(
                    (color) => (
                      <button
                        key={color}
                        aria-label={`Color ${color}`}
                        aria-pressed={settings.color.toUpperCase() === color}
                        style={{ background: color }}
                        onClick={() => setSettings((s) => ({ ...s, color }))}
                      />
                    ),
                  )}
                  <label>
                    Size{" "}
                    <input
                      type="range"
                      min="2"
                      max="40"
                      value={settings.size}
                      onChange={(e) =>
                        setSettings((s) => ({
                          ...s,
                          size: Number(e.target.value),
                        }))
                      }
                    />
                  </label>
                  <label>
                    Custom color{" "}
                    <input
                      type="color"
                      value={settings.color}
                      onChange={(e) =>
                        setSettings((s) => ({ ...s, color: e.target.value }))
                      }
                    />
                  </label>
                </div>
              </fieldset>
            )}
            {result && game?.result && (
              <section className="room-panel room-result-overlay">
                <h2>{me.solved ? "You got it!" : "Round complete"}</h2>
                <p>Your round: {game.result.deltas[me.id] ?? 0} points</p>
                {game.result.components?.[me.id] &&
                  Object.entries(game.result.components[me.id]).map(
                    ([key, value]) => (
                      <p key={key}>
                        {key.replace(/([A-Z])/g, " $1")}: {value}
                      </p>
                    ),
                  )}
                <p>
                  Next drawer:{" "}
                  {snap.players.find((p) => p.id === game.result?.nextDrawerId)
                    ?.profile.name ?? "Waiting"}
                  {game.result.countdown !== undefined
                    ? ` · ${game.result.countdown}s`
                    : ""}
                </p>
              </section>
            )}
          </section>
          <aside className="room-chat-column">
            <div className="room-chat-order">
              <section
                className={`room-panel room-chat ${me.solved ? "is-solved" : ""}`}
              >
                <h2>
                  {drawing && role === "guesser" ? "Your guesses" : "Room chat"}
                </h2>
                <div className="room-messages" aria-live="polite">
                  {snap.chat.map((m) => (
                    <p key={m.id}>
                      <strong>
                        {snap.players.find((p) => p.id === m.playerId)?.profile
                          .name ?? "Room"}
                        :{" "}
                      </strong>
                      {m.text}
                    </p>
                  ))}
                </div>
                <form onSubmit={send}>
                  <input
                    aria-label={
                      drawing && role === "guesser"
                        ? "Your guess"
                        : "Message the room"
                    }
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    disabled={
                      result || connection !== "connected" || !!me.solved
                    }
                    placeholder={
                      drawing && role === "guesser"
                        ? "Type your guess…"
                        : "Say something…"
                    }
                  />
                  <button
                    className="room-button"
                    disabled={
                      result || connection !== "connected" || !!me.solved
                    }
                  >
                    Send
                  </button>
                </form>
              </section>
            </div>
            <AiCard game={game} result={result} />
          </aside>
        </div>
      )}
    </main>
  );
}
