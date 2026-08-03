# Eval & CI tooling for swandev — spec

Status: APPROVED (2026-08-03 — user accepted all ledger defaults)
Date: 2026-08-03
Base: stacked on `feat/v2-spec-driven-workflow` (PR #3); PR targets that branch
until #3 merges, then retargets main.

## Goal

Make plugin quality measurable so future changes can be judged: deterministic
structural checks run in CI on every PR; model-dependent evals (routing
accuracy, end-to-end behavior) run locally via `make` and are mandated by a
repo-level skill before any skill-surface PR.

## Non-goals

- No API-key-based eval runner — Tier 2/3 use `claude -p` with existing local
  auth, so they cannot run in CI (no credentials there; that is why they are
  Makefile targets, not workflows).
- No baseline/regression bookkeeping — pass/fail is an absolute floor.
- No judgment of skill *instruction* quality beyond the e2e scenarios; routing
  accuracy + hard-gate behavior is the measured surface.

## Deliverables

### 1. `make lint` + Tier 1 CI (deterministic, free)

`scripts/lint.py` (python3 stdlib only), run by both `make lint` and a GitHub
Actions workflow `.github/workflows/lint.yml` (ubuntu-latest, checkout +
`make lint`) on every PR and push to main. Checks, each with a clear error
message:

1. All `evals/*.eval.json` and `.claude-plugin/*.json` parse; eval files are
   non-empty arrays of exactly `{"query": str, "should_trigger": bool}`.
2. Every `skills/*/SKILL.md` has frontmatter `name:` matching its directory and
   a non-empty single-line `description:`.
3. Every skill has an eval file and every eval file has a skill
   (`skills/<name>/` ↔ `evals/<name>.eval.json`, both directions).
4. Dangling references: no `swandev:<name>` in `skills/`, `evals/`,
   `README.md`, `.claude-plugin/` where `<name>` is not an existing skill
   directory (generalizes the removed-skill grep — catches future renames too).
5. Manifest sync: `plugin.json` and `marketplace.json` agree on version and
   description (the `claude plugin tag` invariant, replicated in python so CI
   needs no CLI).
6. **Context footprint budget:** estimated tokens (total description chars / 4)
   across all skill frontmatter descriptions must be ≤ BUDGET; prints the
   current number every run so growth is visible in every CI log.

### 2. `make eval` — Tier 2 routing accuracy (headless, local)

`scripts/routing_eval.py` (python3 stdlib only):

- Builds one routing prompt: the seven skills' frontmatter descriptions
  (exactly as loaded from `skills/*/SKILL.md`) + the eval query + the
  instruction to reply with ONLY a skill name or `none`.
- For each query in every `evals/*.eval.json`, invokes
  `claude -p --model claude-haiku-4-5 <prompt>` as a subprocess, N_CONCURRENT
  at a time; one vote per query.
- Scores: a `should_trigger: true` query is correct iff the reply names that
  eval's skill; a `should_trigger: false` query is correct iff the reply is
  anything else (another skill or `none`).
- Prints a per-skill table (accuracy, false-trigger count, missed-trigger
  count) plus overall accuracy, and writes `eval-results.json` (gitignored)
  for the PR body.
- **Gate:** exit non-zero if overall accuracy < 90% or any skill < 80%.
- Malformed/unparseable model replies count as wrong answers, not crashes.

### 3. `make e2e` — Tier 3 behavioral scenarios (headless, local)

`scripts/e2e_eval.py` + `scripts/e2e/scenarios.json`. Each scenario runs
`claude -p --plugin-dir <repo> --model claude-haiku-4-5 --output-format
stream-json --verbose --max-turns 6` in a fresh temp dir (git-inited, empty),
then asserts on the emitted event stream.

**Amendment (2026-08-03, evidence-based):** scenarios invoke their skill
EXPLICITLY (`/swandev:<skill> <request>` as the prompt) and assert on gate
behavior only. Headless `-p` sessions load plugin skills and expose the Skill
tool, but neither Haiku nor Sonnet proactively invokes skills there — even
when the system prompt demands it (reproduced across 2 models × 7 runs). Auto-
invocation propensity is a harness property, not plugin quality; routing
quality is already Tier 2's job. Tier 3 measures: once a skill is active, do
its hard gates hold?

| ID | Prompt | Pass condition (plus: no Write/Edit/NotebookEdit in any) |
|----|--------|----------------|
| specifying-gates | "/swandev:specifying let's build a CLI that renames files in bulk" | final text asks at least one question (regex `\?`) — interrogates before building |
| implementing-refuses | "/swandev:implementing implement batch 2" | final text mentions the missing batch plan (regex `batch plan|batching|no .*plan|approved plan`) |
| batching-defers | "/swandev:batching the spec is approved, slice it into batches" | final text asks for the spec (regex `spec`) |

- Permissions: run with `--allowedTools "Skill,Read,Glob,Grep,Bash(git *)"` so
  writes are impossible by construction and nothing prompts interactively.
- **Gate:** exit non-zero if any scenario fails; print per-scenario pass/fail
  with the offending evidence (tool call or missing pattern).
- Scenarios are data (`scenarios.json`): adding one is a data change, not code.

### 4. `Makefile`

Targets: `lint`, `eval`, `e2e`, and `test` = `lint eval e2e`. No other build
system exists in the repo; the Makefile is the single entry point humans and
skills use.

### 5. Repo-level skill: `.claude/skills/pre-pr-gate/SKILL.md`

Project-scoped (loads only when working in this repo; NOT shipped in the
plugin's `skills/`). Rule it enforces, mechanically:

- Before pushing or opening ANY PR from this repo, run `make lint`.
- If `git diff <base>...HEAD --name-only` touches `skills/**`, `evals/**`, or
  `.claude-plugin/**` → additionally run `make eval` and `make e2e`; the PR
  body must include the routing-accuracy table and e2e results; a failing
  floor BLOCKS the PR — fix or explicitly get user sign-off on the regression.
- Docs/README-only diffs: `make lint` only.

### Housekeeping

- `.gitignore` += `eval-results.json`.
- README gets a short "Quality checks" section documenting the three tiers and
  that Tier 2/3 need a logged-in `claude` CLI.

## Decision log (all ledger entries resolved by user, 2026-08-03)

| # | Question | Decision |
|---|----------|----------|
| 1 | Context-footprint BUDGET | 2500 estimated tokens (if current footprint already exceeds 2000, budget = current + 25%, rounded up to nearest 100) |
| 2 | Tier 2 concurrency / votes | 8 concurrent `claude -p` processes, 1 vote per query |
| 3 | Tier 2/3 eval model | `claude-haiku-4-5` via `--model` |
| 4 | e2e `--max-turns` | 6 |
| 5 | Batch delivery | sequential commits in ONE stacked PR (per-batch PRs impossible while base #3 is unmerged) |

## Batches (v2-style slices)

1. **B1 — lint + CI:** Makefile (`lint` target), `scripts/lint.py`, workflow.
   Observable: `make lint` passes locally; green "lint" check appears on the PR.
2. **B2 — routing eval:** `eval` target + `scripts/routing_eval.py` + gitignore.
   Observable: `make eval` prints the table and exits per the floor.
3. **B3 — e2e eval:** `e2e` + `test` targets, `scripts/e2e_eval.py`, scenarios.
   Observable: `make test` runs all three tiers.
4. **B4 — pre-pr-gate skill + README:** `.claude/skills/pre-pr-gate/SKILL.md`,
   README section. Observable: opening a session in the repo shows the skill;
   it mandates the gates above.

## Acceptance for the whole change

- `make test` passes end-to-end on this branch with a logged-in `claude` CLI.
- The lint workflow runs green on the stacked PR.
- Routing eval floor passes on the current seven skills (if it doesn't, that's
  a real finding — fix descriptions or present the failure, never lower the
  floor silently).
