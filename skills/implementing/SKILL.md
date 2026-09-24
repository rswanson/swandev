---
name: implementing
description: Use this when an approved batch plan (from swandev:batching) has a pending batch and the user wants it built — ONE invocation takes ONE batch from pending to a CI-green PR that the USER merges. Trigger on "implement batch N", "next batch", "start building", "kick off the first batch", or "keep going" right after a batch's PR merges. You ORCHESTRATE only; all code is written by fresh Opus subagents (an implementer, then a fresh-context reviewer). Do NOT trigger without an approved batch plan — that's swandev:batching (or swandev:specifying if no spec exists); an unexpected defect mid-batch routes to swandev:debugging; an explicitly requested deep audit is swandev:tribunal.
---

# Implementing

Take exactly one batch from the approved batch plan to a merge-ready PR, then
STOP. The user merges; the next invocation takes the next batch.

## Model split (hard rule)

You (the session model) orchestrate: dispatch, evaluate, ship. You do NOT write
implementation code or tests yourself. All code comes from **fresh
subagents** via the Agent tool:

- **Implementer** (`model: 'opus'`) — builds the batch in the batch worktree,
  with tests that cover its acceptance criteria.
- **Reviewer** (`model: 'opus'`) — fresh context by design: gets ONLY the diff
  and the batch's acceptance criteria, never the implementation conversation.
- **Fixer** (`model: 'sonnet'`) — applies the reviewer's findings. Narrow and
  pre-diagnosed work; the serial path stays on Opus, this does not need to.

## Per-batch loop

1. **Preflight.** Read the batch plan; identify the target batch (the first
   `pending` one unless the user named one). Confirm the previous batch is
   `merged` — if its PR is still open, STOP and ask the user; never build on an
   unmerged batch. Update main, create a fresh worktree + branch for this batch
   (`git worktree add ../<repo>-worktrees/<batch-id> -b feat/<batch-id>` from
   updated main). Mark the batch `in-progress` in the batch doc.
2. **Dispatch the implementer** (Opus, fresh):

   ```text
   Implement batch <ID>: <title> in worktree <path> (branch <branch>).

   User-visible outcome: <from batch entry>
   Acceptance criteria:
   <numbered list from batch entry>
   Relevant spec excerpt:
   <paste the spec sections this batch implements>

   Rules:
   - Every acceptance criterion ends up covered by a test, at the level this
     project already tests at (match the existing suite; extend an existing
     test file before creating a new one). Write tests whenever it is natural
     — before, alongside, or after the code. No mandated red step, no
     separate commit for failing tests.
   - Keep the suite lean: roughly one focused test per criterion. No tests
     for trivial glue, getters, or framework behavior; no tests that restate
     the implementation or assert on mocks.
   - Run the project's formatter, linter, and full test suite before finishing.
   - Touch only what this batch needs; no drive-by refactors.
   - Return: files changed, test commands with their output, and anything you
     could not satisfy.
   ```

3. **Dispatch the reviewer** (Opus, fresh context):

   ```text
   Review this diff against the batch's acceptance criteria. You have no other
   context, by design. Run `git diff main...HEAD` in <worktree>.

   Acceptance criteria:
   <numbered list>

   Check: (a) every criterion is exercised by a test, and the tests are
   proportionate — redundant or implementation-detail tests are findings too;
   (b) correctness of the implementation; (c) code quality as you would
   hold a PR to. Findings only, no fixes: file:line, what, severity
   (blocker / major / minor). Return the single word "clean" if nothing rises
   to a finding.
   ```

4. **Fix loop.** Relay findings to a fresh Sonnet fix pass (`model: 'sonnet'`)
   in the same worktree; re-review with the Opus reviewer until it returns
   clean. If the same finding survives two fix passes, stop and show the user.
5. **Ship.** Run the full local checks yourself (formatter, linter, tests —
   stack-appropriate, e.g. `cargo fmt --check && cargo clippy && cargo test`).
   Push. Open the PR with the batch's outcome + acceptance criteria in the
   body. Watch CI to green (`gh pr checks --watch`). Update the batch doc
   status, hand the user the PR link, and STOP. The user merges.
6. **Next invocation's preflight** marks the batch `merged` and proceeds to the
   next pending batch.

## Failure routing

- An unexpected defect (code that already worked now failing, as opposed to a
  criterion not yet implemented) → `swandev:debugging` for root cause, then
  resume the loop.
- The user wants a heavyweight audit (typically the final batch) →
  `swandev:tribunal`, explicitly invoked only.

## Hard rules

- One invocation, one batch. Never start batch N+1 in the same run, even if
  the user pre-approved the plan — merged main is the required starting state.
- Never merge the PR yourself.
- Never skip the reviewer, even for tiny batches.
