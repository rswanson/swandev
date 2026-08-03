---
name: batching
description: Use this AFTER a spec is approved (via swandev:specifying) and BEFORE any code, to slice the spec into the smallest strictly-serial batches that are each independently deployable — merges to main with CI green, main stays releasable — and user-visible. Trigger when the user says "slice/batch the spec", "break this into deployable chunks", "smallest shippable pieces", "what's the build order", or right after spec approval with no batch plan yet. If no approved spec exists, defer to swandev:specifying; when the user wants to build a batch from an approved batch plan, that's swandev:implementing. Stops at the approved batch plan; writes no code.
---

# Batching

Slice an approved spec into the smallest serially-ordered batches that are each
deployable and testable on their own. The batch plan is the deliverable.

## Batch definition (every clause required)

- A **thin vertical slice with a user-visible behavior change**. No dark code,
  no feature flags — if nothing observable changed after merge, it is not a
  valid batch.
- The **smallest** change meeting that bar. If a batch can be split into two
  slices that are each independently deployable and observable, split it.
- **Deployable:** merges to main with CI green; main remains releasable after.
- **Testable:** numbered acceptance criteria concrete enough that failing tests
  can be written directly from them, plus a one-line "how to observe it".
- **Slice test** every batch must pass: *"If we stopped after this batch, did
  we ship something coherent and observable?"*

## Ordering

Strictly serial. Batch N is planned assuming batches 1..N−1 are merged to main.
No waves, no parallel tasks, no cross-batch file bookkeeping.

## Each batch entry

```markdown
## B<N>: <title>
- **Status:** pending | in-progress | merged
- **User-visible outcome:** <1–2 sentences of observable behavior>
- **Acceptance criteria:**
  1. <concrete, test-derivable>
  2. ...
- **How to observe:** <command / UI action that shows the change>
- **Touches:** <files/areas expected>
```

## Rules

- No placeholders: no "TBD", "TODO", "handle edge cases later", "criteria to be
  refined". A vague criterion is a batching failure.
- If slicing exposes a question the spec doesn't answer, ASK THE USER (or send
  it back through `swandev:specifying` as a spec amendment). Never assume.
- Present the batch list (IDs, titles, outcomes) for user approval BEFORE
  writing the full plan detail if the split is contentious; always get explicit
  approval of the final plan.

## Save and hand off

Work in the feature worktree (never main). Save to
`docs/batches/YYYY-MM-DD-<topic>-batches.md`, commit. After user approval,
invoke `swandev:implementing` for the first pending batch. That is the ONLY
skill you invoke next.
