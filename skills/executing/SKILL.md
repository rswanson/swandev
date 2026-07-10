---
name: executing
description: Use this when you have an approved implementation plan (from swandev:planning) and want to IMPLEMENT THE WHOLE PLAN, not a single task. Trigger when the user says "execute the plan", "run the plan", "implement the plan", "let's build all of it", "start the implementation", "work through the plan/tasks", or kicks off a multi-task plan. Do NOT trigger for a single scoped task or one-off change ("implement task 3", "write the code for X") — that's swandev:tdd directly; or before an approved plan exists — that's swandev:planning or swandev:brainstorming.
---

# Executing Plans (parallel-first)

Run an approved plan to completion, exploiting parallelism. Independent tasks run concurrently; serial only where dependencies actually require it.

## Read the plan's structure

The plan (from `swandev:planning`) groups tasks into **waves**. Within a wave, tasks are independent — no dependency between them and disjoint `Touches:` file sets — so they run concurrently. Waves run in order, with a barrier between them: every task in wave N is implemented, reviewed, and integrated before wave N+1 starts.

If the plan has no wave/`Touches:` annotations, either send it back to `swandev:planning` to add them, or fall back to serial execution — but say which you're doing.

## Per wave

1. **Dispatch independent tasks in parallel**, one implementer per task, each in its **own isolated git worktree** so concurrent commits never race on the shared index.
   - Preferred mechanism here: the **Workflow tool** — `parallel()` / `pipeline()` with `isolation: 'worktree'`, one task per agent.
   - Or dispatch parallel subagents directly, one worktree per agent.
2. **Each implementer follows `swandev:tdd`** for its task (red → green → refactor → commit).
3. **Run `swandev:reviewing` on each task as it finishes** (don't wait for the whole wave): spec-compliance first, then code-quality; the implementer fixes; re-review until clean.
4. **Integrate each approved task** back into the feature branch. Disjoint `Touches:` sets → clean merges. If a merge conflicts, the wave grouping was wrong — stop and fix the plan's grouping before continuing.
5. **Barrier:** once all of the wave's tasks are integrated and green, run the wave's stack checks, then start the next wave.

## Why this is safe where superpowers went serial

superpowers forbids parallel implementers because they race on a shared worktree. **Per-task worktree isolation removes the race**: each agent has its own working tree and index, and integration is a sequence of clean merges of changes the plan declared disjoint. Parallelism is only ever applied to tasks the plan marked independent — never guessed.

## When NOT to parallelize

- A single scoped change → use `swandev:tdd` directly; no orchestration needed.
- A dependency chain → run those tasks in order (later waves).
- Plan lacks wave/`Touches:` annotations → serial, or send back to planning.

## Completion

Keep `swandev:reviewing` on every task — parallelism does not relax review. After the final wave, run the full stack check suite, confirm green, then hand off to `swandev:pr` to ship.
