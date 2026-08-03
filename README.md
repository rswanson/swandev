# swandev

Spec-driven development workflow skills for Claude Code, packaged as a plugin:
interrogate an idea into a high-detail spec, slice it into the smallest
deployable batches, ship each batch as its own CI-green PR — plus an optional
adversarial deep-audit branch.

## Skills

- `swandev:specifying` — idea → high-detail spec via one-question-at-a-time
  dialogue; an assumption ledger blocks approval until every unknown is
  user-resolved
- `swandev:batching` — approved spec → strictly serial batch plan; every batch
  is the smallest user-visible vertical slice that merges with CI green
- `swandev:implementing` — one batch → one merge-ready PR; fresh Sonnet
  subagents write acceptance-tests-first code and review it fresh-context,
  the session model orchestrates
- `swandev:debugging` — root-cause-first debugging discipline
- `swandev:prosecuting` — one-lens adversarial reviewer: exhaustive case that a
  diff is bad, written to a findings file
- `swandev:judging` — verify/score adversarial findings against the code,
  user-gated dispatch of fixes to Sonnet implementers
- `swandev:tribunal` — orchestrate the adversarial pipeline: parallel
  prosecutors (one per lens) → one judge

## Workflow loop

```
specifying ──→ batching ──→ implementing (batch 1) ──→ PR, CI green ──→ you merge
   (spec)      (slices)     implementing (batch 2) ──→ ...
                            implementing (batch N) ──→ done
```

`specifying` builds the spec section by section, refusing approval while any
assumption-ledger entry is unresolved — the model never runs on silent
assumptions. `batching` slices the approved spec into strictly serial batches:
each the smallest user-visible vertical slice that merges to main with CI
green (trunk-based — "deployable" means main stays releasable; no dark code,
no feature flags). `implementing` takes exactly one batch per invocation to a
merge-ready PR and stops — you merge, then the next invocation picks up the
next batch. `debugging` is invoked any time an unexpected defect appears.

**Model tiering:** `specifying`, `batching`, and all orchestration run on the
session model (Opus/Fable). All code inside `implementing` is written by fresh
Sonnet subagents — an acceptance-tests-first implementer, then a fresh-context
reviewer that sees only the diff and the batch's acceptance criteria.

## Adversarial deep audit (optional branch)

For big changes and pre-merge moments, `tribunal` runs the heavyweight audit —
deliberately the opposite temperament of `implementing`'s fast per-batch
review gate (which is never replaced by this):

```
tribunal ─→ N× prosecuting (parallel, one lens each) ─→ judging
             writes .reviews/<run>/<lens>.findings.md      │
                                       verify → user gate → Sonnet fixers
```

Cost tiering: mechanical lenses (correctness, security, performance, tests) run
on Sonnet; taste lenses (architecture, API ergonomics, merge-worthiness) and the
judge run on the session model. Artifacts land in a gitignored `.reviews/`
directory. The merge-worthiness prosecutor argues the diff shouldn't merge at
all; a sustained motion reaches the user before any per-finding fixes.

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

## License

MIT — see [LICENSE](LICENSE).
