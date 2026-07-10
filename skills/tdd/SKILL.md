---
name: tdd
description: Use this when you are ABOUT TO WRITE CODE for a feature/bugfix that already has a plan or a clearly-scoped single change, BEFORE writing implementation code. Trigger when the user says "implement task N", "start/do task N", "next task", "write the code", "let's code this up", "build out X now"/"build it", or starts executing a plan task-by-task — a direct imperative to write code for a specific, clearly-scoped change is tdd whether or not a written plan exists. Also owns three NON-bug failure cases: the planned red-step failing test, compile/undefined-symbol errors from not-yet-written code, and new error-handling/resilience branches for expected external failures (flaky network, oversized input, rate limits). Do NOT trigger on "how should we implement X" or requests for steps/sequencing (that is swandev:planning), on brand-new feature requests where the approach is still undecided (that is swandev:brainstorming), or when code that should already work is failing for an unknown reason (that is swandev:debugging).
---

# Test-Driven Development

Write the test first. Always. The test defines done.

## The loop (one cycle per behavior)

1. **Red** — write the smallest failing test for the next behavior. Run it. Confirm it fails for the right reason (not a typo/import error).
2. **Green** — write the minimal code to pass. Run the test. Confirm it passes.
3. **Refactor** — clean up with tests green. Re-run.
4. **Commit** — small, frequent commits with imperative messages.

Never write implementation before a failing test exists. Never write more code than the current test demands (YAGNI).

## Fast path (atomic changes)

The full loop is right for anything with new behavior surface. For a **genuinely atomic** change it's overkill — collapse the ceremony, don't abandon the discipline.

**Qualifies only if ALL hold:** single file (or a tightly coupled pair), no new public behavior or branching logic, mechanically obvious correctness. Typical: typo/comment, log-message wording, a config/constant value, a dependency bump, a rename, a doc tweak.

**Disqualifies — use the full loop:** any new function/branch/error path, anything touching auth/money/data-migration/security, anything you're not sure is atomic. When in doubt, it's not the fast path.

**Collapsed cycle:** verify the change does what it claims (run the narrowest existing test, or for a non-behavioral change just the relevant project check below) → **one** commit → **inline self-review** in your reply (does it match intent, any obvious breakage?) instead of dispatching `swandev:reviewing`. Skip worktree orchestration. State explicitly that you took the fast path and why it qualified, so the caller can object.

A bugfix never qualifies — it always gets a regression test (full loop).

## Before you start

- Work in a worktree. Confirm `git worktree list` and `git branch --show-current` before editing, not after.
- This skill is the per-task loop. If asked to implement a WHOLE multi-task plan, that's `swandev:executing` (it runs independent tasks in parallel and dispatches each one here). Use this skill directly for a single task or a one-off scoped change.

## Project checks (run before declaring a task done)

Run the project's formatter, linter, build, and test suite — prefer whatever the
repo itself defines (Makefile/justfile targets, `package.json` scripts, pre-commit
hooks, the CI workflow's own steps) over guessing. Examples: `cargo fmt --check` /
`cargo clippy` / `cargo test` for Rust, `go build` / `go vet` / `go test ./...` for
Go, a dry-run/preview for IaC changes.

Run all relevant checks locally before pushing. Never push code that hasn't passed.

## Test design

- One behavior per test. Name tests for the behavior, not the function.
- Test observable behavior through public interfaces, not internals.
- Prefer real inputs/outputs over mocks where practical.
- A bugfix ALWAYS gets a regression test first — one that fails before the fix and passes after.

## When a test won't pass

Stop guessing. Invoke `swandev:debugging` — root cause before fixes. Once debugging has found the root cause, return to this loop to write the failing regression test, then the fix. Do not implement a fix for an observed failure until debugging has confirmed the root cause.

## When the feature is complete

Run the full relevant check suite, confirm green, then hand off to `swandev:pr` to ship.
