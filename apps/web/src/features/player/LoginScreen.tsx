"use client";

import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  CRAYON_COLORS,
  DEFAULT_AVATAR,
  type AvatarConfig,
  type AvatarShape,
  type AvatarExpression,
  type CrayonColor,
} from "../../contracts/player";
import { Avatar } from "./Avatar";
import { readPlayerProfile, savePlayerProfile } from "./profile";
import "./player.css";

const shapes: AvatarShape[] = ["pebble", "droplet", "spark"];
const expressions: AvatarExpression[] = ["smile", "wink", "wow"];
const colors = Object.keys(CRAYON_COLORS) as CrayonColor[];
const pick = <T,>(items: T[]): T =>
  items[Math.floor(Math.random() * items.length)];
const title = (s: string) => s[0].toUpperCase() + s.slice(1);
const code = () =>
  Array.from({ length: 6 }, () =>
    pick("ABCDEFGHJKLMNPQRSTUVWXYZ23456789".split("")),
  ).join("");

type BobStyle = CSSProperties & {
  "--bob-duration": string;
  "--bob-delay": string;
  "--bob-lift": string;
};
export default function LoginScreen() {
  const router = useRouter();
  const params = useSearchParams();
  const [name, setName] = useState("");
  const [avatar, setAvatar] = useState<AvatarConfig>(DEFAULT_AVATAR);
  const [room, setRoom] = useState(params.get("code") ?? "");
  const [error, setError] = useState("");
  const [motion, setMotion] = useState<BobStyle[]>([]);
  useEffect(() => {
    const profile = readPlayerProfile();
    // Browser storage is only available after the static page hydrates.
    if (profile) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setName(profile.name);
      setAvatar(profile.avatar);
    }
    // Randomize only after hydration to keep server and client markup consistent.
    setMotion(
      [0, 1, 2, 3].map((i) => ({
        "--bob-duration": `${2.5 + i * 0.5 + Math.random() * 0.4}s`,
        "--bob-delay": `${[-1.3, -2.1, -0.7, -1.8][i]}s`,
        "--bob-lift": `${[-6, -10, -8, -7][i]}px`,
      })),
    );
  }, []);
  function enter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submitter = (event.nativeEvent as SubmitEvent)
      .submitter as HTMLButtonElement | null;
    const joining = submitter?.value === "join";
    const cleanName = name.trim();
    const cleanRoom = room.trim();
    if (!cleanName || cleanName.length > 24) {
      setError("Please enter a name of 1–24 characters.");
      return;
    }
    if (joining && !cleanRoom) {
      setError("Please enter a room code.");
      return;
    }
    savePlayerProfile({ name: cleanName, avatar });
    router.push(
      `/room/?code=${encodeURIComponent(joining ? cleanRoom : code())}`,
    );
  }
  function randomize() {
    let next: AvatarConfig;
    do {
      next = {
        shape: pick(shapes),
        expression: pick(expressions),
        color: pick(colors),
      };
    } while (
      next.shape === avatar.shape &&
      next.expression === avatar.expression &&
      next.color === avatar.color
    );
    setAvatar(next);
  }
  return (
    <main className="player-login">
      <header className="player-header">
        <img src="/design/assets/more-than-meets-the-ai-icon.png" alt="" />
        <strong>
          More Than
          <br />
          Meets the AI
        </strong>
      </header>
      <div className="player-login-content">
        <section className="player-art">
          <p className="player-eyebrow">Bring your best bad drawing.</p>
          <h1>
            Little doodles.
            <br />
            Big guesses.
          </h1>
          <div className="player-stage">
            <div
              className="player-bob player-decor player-star"
              style={motion[0]}
            >
              <svg viewBox="0 0 80 80" aria-hidden="true">
                <path
                  d="m40 5 9 24 26 9-25 11-9 26-11-25L5 40l24-10Z"
                  fill="#FF57B5"
                  stroke="#181321"
                  strokeWidth="3"
                  strokeLinejoin="round"
                />
                <path
                  d="m29 33 6 4m14 5 5-1"
                  fill="none"
                  stroke="#181321"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <div
              className="player-bob player-decor player-brush"
              style={motion[1]}
            >
              <img
                src="/design/assets/more-than-meets-the-ai-icon.png"
                alt=""
              />
            </div>
            <div className="player-bob player-hero" style={motion[2]}>
              <Avatar avatar={avatar} label="Your paint character preview" />
            </div>
            <div
              className="player-bob player-decor player-splash"
              style={motion[3]}
            >
              <svg viewBox="0 0 80 80" aria-hidden="true">
                <path
                  d="M40 15C44-4 63 4 58 22c17-10 30 8 12 18 18 7 10 28-9 20 3 20-20 24-22 4-13 16-30 1-17-13C2 50 1 28 23 30 10 14 29 0 40 15Z"
                  fill="#37D66B"
                  stroke="#181321"
                  strokeWidth="3"
                />
                <circle
                  cx="42"
                  cy="39"
                  r="10"
                  fill="#FFE83D"
                  stroke="#181321"
                  strokeWidth="3"
                />
              </svg>
            </div>
            <span className="player-name-tag">
              {name.trim() || "Your name"}
            </span>
          </div>
          <p>
            A shape. A face. A splash of color.
            <br />
            Make a little creature that&apos;s all you.
          </p>
        </section>
        <form className="player-form" onSubmit={enter} noValidate>
          <div>
            <p className="player-eyebrow">Meet your paint pal.</p>
            <h2>Make your mark.</h2>
          </div>
          <label className="player-field">
            Your name
            <input
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError("");
              }}
              maxLength={24}
              autoComplete="nickname"
              placeholder="What should we call you?"
            />
          </label>
          <fieldset>
            <legend>Pick a shape</legend>
            <div className="player-options">
              {shapes.map((shape) => (
                <button
                  key={shape}
                  type="button"
                  aria-pressed={avatar.shape === shape}
                  onClick={() => setAvatar({ ...avatar, shape })}
                >
                  <Avatar avatar={{ ...avatar, shape }} />
                  {title(shape)}
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Make a face</legend>
            <div className="player-options">
              {expressions.map((expression) => (
                <button
                  key={expression}
                  type="button"
                  aria-pressed={avatar.expression === expression}
                  onClick={() => setAvatar({ ...avatar, expression })}
                >
                  {title(expression)}
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Add your color</legend>
            <div className="player-colors">
              {colors.map((color) => (
                <button
                  key={color}
                  type="button"
                  className="player-color"
                  style={{ background: CRAYON_COLORS[color] }}
                  aria-label={`${title(color)} character`}
                  aria-pressed={avatar.color === color}
                  onClick={() => setAvatar({ ...avatar, color })}
                />
              ))}
            </div>
          </fieldset>
          <button
            type="button"
            className="player-button player-random"
            onClick={randomize}
          >
            ✦ Surprise me
          </button>
          <div className="player-room">
            <button
              className="player-button player-create"
              type="submit"
              value="create"
            >
              Create a room →
            </button>
            <div className="player-join">
              <label className="player-field">
                Already got a code?
                <input
                  value={room}
                  onChange={(e) => {
                    setRoom(e.target.value);
                    setError("");
                  }}
                  placeholder="Room code"
                  maxLength={32}
                />
              </label>
              <button
                className="player-button player-join-button"
                type="submit"
                value="join"
              >
                Join room
              </button>
            </div>
            {error && (
              <p className="player-error" role="alert">
                {error}
              </p>
            )}
          </div>
        </form>
      </div>
    </main>
  );
}
