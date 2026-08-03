# swandev v2 — spec-driven, batch-deployed workflow (DRAFT)

Status: DRAFT — under user review
Date: 2026-08-03

## Overview

v2 replaces the v1 workflow chain with a spec-driven development loop built around
one idea: **enumerate a high-detail spec through relentless user clarification,
then ship it as a series of the smallest independently deployable, testable
vertical slices.** The model never runs on large assumptions — every unknown is
surfaced to the user before it becomes spec text.

```
specifying ──→ batching ──→ implementing (batch 1) ──→ PR, CI green ──→ user merges
   (spec)      (slices)     implementing (batch 2) ──→ ...
                            implementing (batch N) ──→ done
```

## Goals

- A spec process that extracts maximum user input and forbids silent assumptions.
- Work sliced into the smallest batches that are each deployable (merged to main,
  CI green, main always releasable) and testable (concrete acceptance criteria,
  verified by tests and observable behavior).
- Cheap, repeatable batch execution: Sonnet subagents implement; the session
  model (Opus/Fable) does the thinking-heavy phases and orchestration.
- Smaller context footprint: v1 workflow skills are removed, not merely bypassed.

## Non-goals

- No actual deployment step. "Deployable" means merged + shippable (trunk-based):
  every batch ends as a CI-green PR on main that could be released at any time.
- No feature-flag infrastructure. Every batch is user-visible on its own; there
  is no dark code to gate.
- No parallel execution of batches. Batches are strictly serial by design.
- No rebuild of the v1 `pr` skill; PR mechanics fold into `implementing`.

## Skill inventory changes

| Action  | Skills |
|---------|--------|
| Remove  | `brainstorming`, `planning`, `executing`, `tdd`, `reviewing`, `pr` |
| Add     | `specifying`, `batching`, `implementing` |
| Keep    | `debugging`, `tribunal`, `prosecuting`, `judging` (prose updated to drop references to removed skills) |

## Skill 1: `specifying` — interrogative spec building

**Trigger:** a new feature/project idea with no approved spec. The entry point of
the v2 workflow (replaces `brainstorming`).

**Model:** runs in the main session (Opus/Fable default).

**Process:**

1. Explore the codebase, docs, and recent commits before asking anything.
2. Build the spec **section by section**, in order: goals & non-goals, users &
   flows, scope boundaries, behavior (interfaces, data, commands), edge cases &
   failure modes, testing & acceptance. Each section is presented to the user
   and gated on their approval before the next begins.
3. **Assumption ledger** — the core mechanism. Any unknown encountered while
   drafting becomes a ledger entry:

   ```
   | # | Question | Proposed default | Status |
   ```

   An entry resolves ONLY when the user answers it or explicitly confirms the
   proposed default. **The spec cannot be approved while any entry is
   unresolved.** Baked-in rule: if the model is about to write "probably",
   "presumably", or "we can assume" — that is a ledger entry, not prose.
4. Question mechanics: AskUserQuestion, one question at a time, multiple-choice
   with a recommendation first where possible. Never batch questions; never
   substitute a guess for an unasked question.
5. Write the spec to `docs/specs/YYYY-MM-DD-<topic>-spec.md` in a git worktree
   (never on main), commit as DRAFT, self-review for placeholders /
   contradictions / unresolved ledger entries, then present for user approval.

**Output / hand-off:** an approved spec document → invoke `swandev:batching`.

## Skill 2: `batching` — slice the spec into minimal deployable increments

**Trigger:** an approved spec exists; no batch plan yet (replaces `planning`).

**Model:** runs in the main session (Opus/Fable default).

**Batch definition (all required):**

- A **thin vertical slice with a user-visible behavior change**. No dark code,
  no feature flags — if nothing observable changed, it is not a valid batch.
- The **smallest** change meeting that bar: if a batch can be split into two
  slices that are each independently deployable and observable, split it.
- **Deployable:** merges to main with CI green; main remains releasable after.
- **Testable:** concrete acceptance criteria, written so failing tests can be
  derived directly from them, plus a short "how to observe it" note.
- **Slice test** every batch must pass: *"If we stopped after this batch, did we
  ship something coherent and observable?"*

**Ordering:** strictly serial. Batch N is planned assuming batches 1..N−1 are
merged. No waves, no parallel tasks, no `Touches:` bookkeeping.

**Each batch entry contains:**

- ID and title
- User-visible outcome (one or two sentences, observable behavior)
- Acceptance criteria (numbered, concrete, test-derivable)
- Files/areas expected to be touched
- Status: `pending` / `in-progress` / `merged` (maintained by `implementing`)

**Rules:** no placeholders — no "TBD", "TODO", "handle edge cases later". If
slicing exposes a question the spec doesn't answer, go back to the user (or to
`specifying` for a spec amendment) rather than assuming.

**Output / hand-off:** `docs/batches/YYYY-MM-DD-<topic>-batches.md`, committed.
The user approves the batch plan before any implementation starts. Then invoke
`swandev:implementing` for batch 1.

## Skill 3: `implementing` — one batch → one merge-ready PR

**Trigger:** an approved batch plan with a pending batch (replaces `executing`,
`tdd`, `reviewing`, and `pr`). One invocation = one batch.

**Model split:** the session model (Opus/Fable) acts as **orchestrator** only —
it dispatches work, evaluates results, and handles the PR. All code is written
by **fresh Sonnet subagents**:

- **Implementer subagent (Sonnet):** receives the batch entry + spec excerpt +
  repo context; works acceptance-tests-first in the batch worktree.
- **Reviewer subagent (Sonnet, fresh context):** receives only the diff, the
  batch's acceptance criteria, and quality guidelines — no implementation
  conversation — and returns findings.

**Per-batch loop:**

1. **Preflight:** confirm the previous batch's status is `merged` (ask the user
   if its PR is still open — never build on an unmerged batch). Update main,
   create a fresh worktree/branch for this batch. Mark batch `in-progress`.
2. **Acceptance tests first:** implementer subagent writes the batch's
   acceptance criteria as failing tests, runs them to confirm they fail for the
   right reason, then implements until green, then refactors. Commits along the
   way.
3. **Fresh-context review:** reviewer subagent checks the diff against the
   acceptance criteria and code quality. Orchestrator relays findings to a fix
   pass (implementer subagent); re-review until clean.
4. **Ship:** run full local checks (format, lint, tests — stack-appropriate),
   push, open the PR with the batch's outcome + acceptance criteria in the body,
   watch CI to green (`gh pr checks --watch`), then hand the user the PR link
   and **stop**. The user merges.
5. On merge (next invocation's preflight), mark the batch `merged` and proceed
   to the next pending batch.

**Failure routing:** an unexpected defect (not the planned red step) routes to
`swandev:debugging`. `swandev:tribunal` remains the explicitly-invoked deep
audit — sensible on the final batch or any batch the user flags.

## Kept skills — required edits

- `debugging`: remove references to `swandev:tdd` and its red-step carve-outs;
  the expected-failure carve-out now points at `implementing`'s acceptance-test
  red step. Fix-execution hand-off references `implementing` instead of `tdd`/`pr`.
- `tribunal` / `prosecuting` / `judging`: update any prose contrasting with
  `swandev:reviewing` (now removed) to instead contrast with `implementing`'s
  per-batch fresh-context review. Cost tiering language stays as-is.

## Repo changes

1. Delete `skills/{brainstorming,planning,executing,tdd,reviewing,pr}/` and
   `evals/{brainstorming,planning,executing,tdd,reviewing}.eval.json` (no pr eval exists).
2. Add `skills/{specifying,batching,implementing}/SKILL.md` with trigger-rich
   descriptions that route between each other and the kept skills.
3. Add `evals/{specifying,batching,implementing}.eval.json` in the existing format.
4. Rewrite `README.md` around the new loop (workflow diagram, skill list,
   model-tiering note, install/update instructions unchanged).
5. Bump `version` to `2.0.0` in `.claude-plugin/plugin.json` AND
   `.claude-plugin/marketplace.json` (must stay in sync); refresh `description`
   and `keywords` in both.

## Testing & acceptance for the v2 build itself

- Each new SKILL.md passes the existing eval format's structural checks (valid
  frontmatter, description with trigger/anti-trigger language).
- `claude --plugin-dir` smoke test: the three new skills load, the six removed
  ones do not appear, kept skills still load.
- Grep check: no SKILL.md or README references a removed skill name.
- `claude plugin tag` validation passes (version sync).

## Decision log (resolved during design dialogue)

| # | Question | Decision |
|---|----------|----------|
| 1 | Fate of v1 skills | Keep debugging + tribunal trio; remove workflow chain AND `pr` |
| 2 | Meaning of "deployable" | Merged + shippable (trunk-based); no deploy step in workflow |
| 3 | Skill decomposition | 3 skills: specifying / batching / implementing |
| 4 | Spec Q&A mechanism | Assumption ledger + per-section approval gates |
| 5 | Merge gate | Auto-PR + CI watch; user merges |
| 6 | In-batch discipline | Acceptance-tests-first per batch (not per-task TDD) |
| 7 | Batch review | Fresh-context subagent review vs acceptance criteria |
| 8 | Dark slices | Not allowed — every batch user-visible (vertical slices only) |
| 9 | Model tiering | specifying/batching + orchestration on session model (Opus/Fable); implementation and review via fresh Sonnet subagents |

## Open questions

None — all ledger entries resolved above.
