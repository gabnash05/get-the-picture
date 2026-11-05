# Login motion

Status: approved for the base frontend in the V2 Lavish review on 4 November 2026, Asia/Manila. The preview-approval prerequisite is satisfied; the base implementation now applies these rules, with reduced-motion behavior verified in the production browser checks.

Read `DESIGN.md` for the Lemon Crayon palette, fonts, spacing, and shapes. This file adds motion behavior without changing those foundations.

## Scope

**Login screen only.** Apply a subtle idle bob to the large character preview and decorative assets on the combined name / character / create-or-join screen.

Keep the name field, character controls, buttons, room-code field, form container, typography, and header static. Do not apply this motion to the game room, roster avatars, canvas, brush cursor, toolbar, chat, or game panels.

## Idle bob

- Animate an outer wrapper, never SVG paths or internal character parts.
- Use the same CSS keyframes for every moving asset: `translateY(0)` at 0% and 100%, and a negative vertical offset at 50%.
- Choose an offset between -6px and -10px per wrapper. The preview uses -8px by default.
- Assign each wrapper a different duration randomized between 2.5s and 4.5s, once when the login screen initializes.
- Apply different negative delays such as -0.7s, -1.3s, and -2.1s so the assets begin at different phases.
- Use a gentle ease-in-out curve and repeat continuously. Do not restart or rerandomize on every form edit or render.
- The optional horizontal figure-eight drift is omitted from this first preview to keep the motion simple.

Example keyframes and scope:

```css
@keyframes login-idle-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(var(--bob-lift, -8px)); }
}

.login-screen .login-idle-wrapper {
  animation: login-idle-bob var(--bob-duration, 3.5s)
    ease-in-out var(--bob-delay, -0.7s) infinite;
}

@media (prefers-reduced-motion: reduce) {
  .login-screen .login-idle-wrapper {
    animation: none;
    transform: none;
  }
}
```

In the React application, assign the randomized values once after client mounting or through a stable client-only initialization. Avoid a server/client hydration mismatch. The login layout must not depend on animation for alignment or usable controls.

## Verification

1. The character and decorative wrappers move gently at different phases and durations.
2. Typing, choosing a character, and using room controls does not move the controls or restart every animation.
3. Entering the game room leaves every roster avatar and canvas control static.
4. Reduced-motion preference stops every login bob while preserving the layout and character customization.

## Login screen implementation brief

Read `DESIGN.md` for colors, fonts, and shapes. Read `LOGIN_MOTION.md` for idle bobbing behavior. Build the login screen with a character creator, name input, and join/create room panel. Apply the idle bob to the character preview and decorative assets on this screen only. Everything else stays static.
