---
name: onboarding
description: Orient agents to this repository before implementation or review.
---

# Onboarding

Use this skill when entering the repository, resuming after losing context, or starting substantial implementation or review. It refreshes understanding from the current checkout; it is not a substitute for reading task-specific code and tests. Keep the pass proportional to the task.

## Workflow

1. **Inspect the live checkout first.** Run `git status --short --branch` and `git diff --stat`. Note staged, unstaged, and untracked work that could overlap the task. Inspect relevant diffs before editing. Treat existing changes as user-owned; do not reset, discard, stage, or commit them unless explicitly asked.
2. **Read repository instructions and overview.** Read `AGENTS.md`, then `README.md`, `CONTEXT.md`, and `SYSTEM-DESIGN.md`. Use `references/repository-map.md` to find the most relevant task-specific sources; do not load every plan for a narrow task.
3. **Follow the task's source trail.** Read the relevant subsystem README, plan, manifest, implementation, and tests. Before changing backend scoring or turn lifecycle, read `docs/BACKEND-SCORING-PLAN.md`. For frontend work, consult the frontend scope/implementation/validation docs and `apps/web/README.md`. For research work, consult `models/guesser/evaluation/README.md` and its project configuration.
4. **Verify status in the current checkout.** Treat code and tests as evidence of what exists now; treat plans as intended behavior and validation reports as historical claims until checks are rerun. Distinguish implemented behavior from fixtures, planned work, and currently verified results. Do not infer an implementation from architecture diagrams, a passing historical report, or an old conversation.
5. **Resolve conflicting guidance explicitly.** Follow applicable `AGENTS.md` requirements and the latest explicit project decisions. If authoritative sources still disagree or leave a consequential design choice open, identify the exact conflict and ask before making that decision. Do not silently choose based only on file modification time.
6. **Hand off a concise orientation.** State the relevant current behavior and boundaries, the paths that govern the task, any dirty-worktree risk, and unresolved decisions or validation limits. Then proceed with the requested work; onboarding itself does not require a repository change.

## Keep this skill current

Update this skill when the onboarding sequence or repository-wide guidance changes. Update `references/repository-map.md` when project areas, authoritative documents, or task routing change. Do not edit either file for ordinary feature changes; keep volatile implementation status out of this guide and verify it from the checkout instead.
