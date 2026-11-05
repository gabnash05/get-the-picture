import { CRAYON_COLORS, type AvatarConfig } from "../../contracts/player";
import "./player.css";

const shapes = {
  pebble:
    "M32 5C48 2 60 16 59 34C61 49 48 60 31 59C12 61 4 48 5 31C3 16 16 4 32 5Z",
  droplet:
    "M32 3C33 14 58 25 58 39C58 52 47 61 32 61C17 61 6 52 6 39C6 25 25 14 32 3Z",
  spark:
    "M31 3Q35 3 39 18Q41 22 53 24Q62 26 58 32Q47 39 46 43Q44 58 38 59Q33 60 27 47Q25 44 14 44Q4 44 7 36Q14 24 17 23Q21 18 23 7Q25 1 31 3Z",
};

export function Avatar({
  avatar,
  className,
  label,
}: {
  avatar: AvatarConfig;
  className?: string;
  label?: string;
}) {
  return (
    <svg
      className={["player-avatar", className].filter(Boolean).join(" ")}
      viewBox="0 0 64 64"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <path
        d={shapes[avatar.shape]}
        fill={CRAYON_COLORS[avatar.color]}
        stroke="#181321"
        strokeWidth="3"
        strokeLinejoin="round"
      />
      <g fill="#181321" stroke="#181321" strokeLinecap="round">
        <circle cx="23" cy="28" r={avatar.expression === "wow" ? 3 : 2.5} />
        {avatar.expression === "wink" ? (
          <path d="M37 29Q42 23 47 29" fill="none" strokeWidth="3" />
        ) : (
          <circle cx="41" cy="28" r={avatar.expression === "wow" ? 3 : 2.5} />
        )}
        {avatar.expression === "wow" ? (
          <ellipse cx="32" cy="42" rx="5" ry="6" />
        ) : (
          <path d="M24 39Q32 49 40 39" fill="none" strokeWidth="3" />
        )}
      </g>
    </svg>
  );
}
