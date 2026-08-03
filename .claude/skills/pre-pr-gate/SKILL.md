---
name: pre-pr-gate
description: Use this before pushing a branch or creating ANY pull request from the swandev repo — trigger on "open a PR", "push this", "ship it", "ready for review", or any PR-creation intent; it decides which make gates must pass first.
---

# Pre-PR Gate

## The iron law

A failing floor BLOCKS the PR. Never lower a floor, never skip a failing
gate — fix the regression, or present the failure to the user and get their
explicit sign-off recorded in the PR body.

## Step 1 — always: `make lint`

Run `make lint`. It must pass. This is Tier 1: deterministic, free, no
`claude` CLI required.

## Step 2 — decide whether Tiers 2/3 are needed

Run `git diff <base>...HEAD --name-only`, where `<base>` is the PR's target
branch.

- If ANY changed path matches `skills/**`, `evals/**`, or
  `.claude-plugin/**` → run `make eval` AND `make e2e`. Both need a
  logged-in `claude` CLI and take a few minutes total.
- If the diff is docs/README-only (no path in those three globs) → skip
  this step; `make lint` alone is sufficient.

## Step 3 — hard gate

- `make lint` failing blocks the PR unconditionally.
- When step 2 ran, `make eval` failing (overall < 90% or any skill < 80%)
  or `make e2e` failing (any scenario) also blocks the PR.
- Do not lower a floor, skip a gate, or wave it through silently. Either
  fix the regression, or stop and get the user's explicit sign-off on the
  specific failure, recorded in the PR body.

## Step 4 — PR body requirements

When step 2 ran, the PR body MUST include:

- The routing-accuracy per-skill table and overall percentage (from
  `make eval`).
- The e2e per-scenario results (from `make e2e`).

## Shorthand

`make test` runs `lint eval e2e` in one shot — use it to run everything
before deciding what the PR body needs.
