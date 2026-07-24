# swandev

Development workflow skills for Claude Code, packaged as a plugin: an
idea → spec → plan → parallel execution → review → PR pipeline, plus an
optional adversarial deep-audit branch.

## Skills

- `swandev:brainstorming` — idea → design/spec via dialogue
- `swandev:planning` — spec → step-by-step implementation plan, grouped into dependency-aware waves
- `swandev:executing` — orchestrate a plan: run each wave's independent tasks concurrently in isolated worktrees
- `swandev:tdd` — the per-task test-first loop (red → green → refactor → commit)
- `swandev:reviewing` — two-stage review (spec-compliance, then code-quality) of a diff or task
- `swandev:prosecuting` — one-lens adversarial reviewer: exhaustive case that a diff is bad, written to a findings file
- `swandev:judging` — verify/score adversarial findings against the code, user-gated dispatch of fixes to Sonnet implementers
- `swandev:tribunal` — orchestrate the adversarial pipeline: parallel prosecutors (one per lens) → one judge
- `swandev:debugging` — root-cause-first debugging discipline
- `swandev:pr` — create a PR with local CI validation

## Workflow loop

```
brainstorming → planning → executing → pr
   (spec)        (waves)   (parallel)   (ship)
                              │
                              ├── per task: tdd → reviewing
                              └── on any failure: debugging
```

Each skill hands off to the next. `executing` runs the plan's independent tasks in
parallel (worktree-isolated), dispatching each to `tdd` then gating it on `reviewing`
(spec-compliance, then code-quality); `debugging` is invoked any time a bug, test
failure, or unexpected behavior appears. For a single one-off change, go straight to
`tdd`. For a **genuinely atomic** change (typo, config value, dep bump), `tdd` has a
**fast path** that collapses the loop to verify → one commit → inline self-review,
skipping worktree orchestration and the separate `reviewing` dispatch.

## Adversarial deep audit (optional branch)

For big PRs and pre-merge moments, `tribunal` runs the heavyweight audit —
deliberately the opposite temperament of `reviewing` (which stays the fast,
confidence-filtered per-task gate and is never replaced by this):

```
tribunal ─→ N× prosecuting (parallel, one lens each) ─→ judging
             writes .reviews/<run>/<lens>.findings.md      │
                              verify → user gate → fixers → integrate
```

**Cost control** is the design constraint on this branch, at three points:

- **Lens selection** — four by default (correctness, security, architectural
  drift, test adequacy). `api-ergonomics`, `performance` and `merge-worthiness`
  are added only when the diff earns them; "run all seven" is an explicit ask.
- **Prosecutor budget** — at most 10 findings per lens, with a severity floor.
  The budget cuts low *value*, never low *confidence*: an uncertain-but-real
  flaw still gets written down, because the judge is what filters.
- **Judge gate** — at most 8 findings are put to the user at once; the rest stay
  recorded in the verdict file rather than dispatched.

Cost tiering: mechanical lenses (correctness, security, performance, tests) run
on Sonnet; taste lenses (architecture, API ergonomics, merge-worthiness) and the
judge run on the session model. Artifacts land in a gitignored `.reviews/`
directory. The merge-worthiness prosecutor argues the diff shouldn't merge at
all; a sustained motion reaches the user before any per-finding fixes. Approved
fixes are merged back into the branch under review — a finding isn't resolved
until its commit is on that branch.

## Install

```
/plugin marketplace add rswanson/swandev
/plugin install swandev@swandev-dev
```

## Updating the installed plugin

The plugin is consumed from a GitHub-source marketplace whose `source` is the repo
root (`"./"`), so **the marketplace is the unit of updates, not the plugin**.
Installing copies a snapshot pinned to the `version` in `.claude-plugin/plugin.json`;
an unchanged version is a no-op. To ship a change:

1. Merge it to `main`.
2. **Bump `version`** in both `.claude-plugin/plugin.json` and
   `.claude-plugin/marketplace.json` (keep them in sync — `claude plugin tag`
   validates this).
3. Restart the session — on startup the marketplace re-syncs from GitHub and applies
   the new version automatically. `claude plugin marketplace update swandev-dev`
   forces an immediate re-sync without restarting.

## Iterating on skills (fast dev loop)

To edit skills without the install/update dance, run a session against a clone:

```
claude --plugin-dir /path/to/swandev
```

`SKILL.md` edits are picked up live; run `/reload-plugins` for hooks/agents/MCP
changes.

## Routing evals

Ten skills with adjacent responsibilities means routing is this plugin's main
failure mode, so it has a test suite: 191 cases in `evals/<skill>/case.yaml`,
each a prompt plus whether that skill must (`expect:`) or must not
(`expect_not:`) be invoked.

```
python3 evals/run.py --parse-only        # free: just checks the case files parse
python3 evals/run.py --tag smoke         # 12 cases, cheap
python3 evals/run.py --skill reviewing   # one skill
python3 evals/run.py                     # all 191 — real model runs, real money
```

Each case is a headless `claude -p` run with the plugin loaded; the runner
records which skills the model actually invoked. Stdlib only, no dependencies.

`claude plugin eval` is the official runner and would replace this — the case
files use its documented `evals/<skill>/case.yaml` layout so the port is
mechanical — but it is early-access gated at time of writing and currently runs
nothing.

**Results are noisy.** One run per case, and routing is not deterministic;
treat a single failure as a signal to re-run, not as a regression. Only the
`validate` workflow gates pushes — evals are `workflow_dispatch` because a full
sweep costs real money.

### Known routing baseline

0.5.0 cut the trigger descriptions hard, then restored the full prose for the
two skills that most need to fire when you *didn't* think to ask for them —
`debugging` and `reviewing`. Measured on the smoke subset, one run per case:

| descriptions | chars | smoke pass rate |
| --- | --- | --- |
| 0.4.0, full trigger prose everywhere | 7,558 | 75% |
| all ten cut to one line | 1,395 | 58% |
| **0.5.0 — eight cut, `debugging`+`reviewing` restored** | **2,862** | **83%** |

**Read these numbers with care.** 12 cases, one run each. In the third arm
`debugging` and `reviewing` passed with description text *identical* to the
first arm, where both failed — that is run-to-run variance, not an improvement
earned by the change. The defensible conclusions are only the coarse ones:
cutting every description hurts intent-based routing, restoring the two
load-bearing ones recovers most of it, and 8 of 10 skills lose nothing
measurable by being one line long.

Explicit invocation is unaffected in every arm — skills fire reliably when
named. What the cut trades away is inference from intent alone, which is the
right trade for a plugin driven by explicit invocation and the wrong one if you
rely on skills firing unprompted.

## License

MIT — see [LICENSE](LICENSE).
