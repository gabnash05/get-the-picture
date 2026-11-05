import {
  CRAYON_COLORS,
  type PlayerProfile,
  type AvatarShape,
  type AvatarExpression,
} from "../../contracts/player";

const KEY = "mtmai.player.v1";
let memory: PlayerProfile | null = null;

function valid(value: unknown): value is PlayerProfile {
  if (!value || typeof value !== "object") return false;
  const p = value as Record<string, unknown>;
  if (
    typeof p.name !== "string" ||
    p.name.trim() !== p.name ||
    p.name.length < 1 ||
    p.name.length > 24 ||
    !p.avatar ||
    typeof p.avatar !== "object"
  )
    return false;
  const a = p.avatar as Record<string, unknown>;
  return (
    ["pebble", "droplet", "spark"].includes(a.shape as AvatarShape) &&
    ["smile", "wink", "wow"].includes(a.expression as AvatarExpression) &&
    typeof a.color === "string" &&
    Object.hasOwn(CRAYON_COLORS, a.color)
  );
}

export function readPlayerProfile(): PlayerProfile | null {
  try {
    if (typeof window === "undefined") return memory;
    const raw = window.localStorage.getItem(KEY);
    if (raw === null) return memory;
    const parsed: unknown = JSON.parse(raw);
    if (!valid(parsed)) return memory;
    memory = parsed;
    return parsed;
  } catch {
    return memory;
  }
}

export function savePlayerProfile(profile: PlayerProfile): void {
  if (!valid(profile)) return;
  memory = { name: profile.name, avatar: { ...profile.avatar } };
  try {
    if (typeof window !== "undefined")
      window.localStorage.setItem(KEY, JSON.stringify(memory));
  } catch {
    /* Memory remains available in this page session. */
  }
}
