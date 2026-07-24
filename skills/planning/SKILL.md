---
name: planning
description: "Turn an approved spec into a saved, wave-structured implementation plan. Invoke explicitly, after a design is approved and before any code."
---

# Planning

Turn a spec into a complete, bite-sized implementation plan. Assume the implementer knows the language but nothing about this codebase or domain.

You write the actual test and implementation code INTO the plan document as a reference — you do NOT create or modify source files here. `swandev:tdd` executes the plan against the real repo.

## Before you start

- A spec should already exist (from `swandev:brainstorming`). If not, go back and brainstorm first.
- Work in a worktree — never edit on main. Confirm with `git worktree list` and `git branch --show-current` before editing.
- Scope check: if the spec spans multiple independent subsystems, split into one plan per subsystem. Each plan must produce working, testable software on its own.

## File structure first

Before defining tasks, map every file you'll create or modify and its single responsibility. Prefer small, focused files. Files that change together live together. This locks in decomposition before task-writing.

## Plan for parallelism (waves)

Don't emit a flat serial list when work is independent. Organize tasks into **waves** so `swandev:executing` can run independent tasks concurrently:

- Each task declares **Depends-on** (task IDs it needs completed first) and **Touches** (the file globs it creates/modifies — usually its Files list).
- A task belongs to the earliest wave that comes *after* every task it depends on.
- **No two tasks in the same wave may share a Touches path.** Same-file tasks go in different waves (or get merged) — otherwise they collide when run concurrently.
- Tasks within a wave have no ordering and run concurrently; waves run in sequence with a barrier (all reviewed + integrated) between them.

Present a short **Execution plan** up front listing the waves and their task IDs, then the full task details. If the work is genuinely sequential (each task needs the previous), say so — one task per wave is correct.

## Task granularity

Each step is ONE action (2–5 minutes), and commit frequently. (The full red→green→refactor→commit structure is specified under "Each task contains" below.)

## No placeholders (these are plan failures)

- No "TBD", "TODO", "implement later", "add error handling", "handle edge cases".
- No "write tests for the above" without the actual test code.
- No "similar to Task N" — repeat the code; tasks may be read out of order.
- Every code step shows the actual code. Every command step shows the exact command and expected output.
- Never reference a type/function/method not defined in some task.

## Each task contains

- **Files:** exact create/modify/test paths.
- **Depends-on / Touches:** task IDs this needs first (empty if none), and the file globs it creates/modifies (for wave-conflict detection).
- **Steps:** the failing test (with code) → run-to-fail (command + expected) → minimal implementation (with code) → run-to-pass (command + expected) → commit (with message).

## Self-review before handoff

- **Spec coverage:** point to a task for every spec requirement; add tasks for gaps.
- **Placeholder scan:** kill every red flag above.
- **Type consistency:** names/signatures used in later tasks match earlier definitions.
- **Wave correctness:** every Depends-on points to a task in an EARLIER wave; no two tasks in the same wave share a Touches path. Fix the grouping if either is violated.

## Present, save, hand off

**Present the plan in the conversation before saving it.** Show the wave structure, the task list with one line each, and any decision you made on the user's behalf. A file path is not a presentation — never ask someone to approve a plan they have not been shown. Wait for approval; a plan is cheap to change now and expensive to change once `swandev:executing` has dispatched from it.

Then save to `docs/plans/YYYY-MM-DD-<feature>.md` and commit it. Hand off to `swandev:executing`, which runs the plan's waves — independent tasks concurrently — dispatching each task to `swandev:tdd`. Do not write implementation code yourself; the plan is the deliverable.
