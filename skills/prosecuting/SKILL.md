---
name: prosecuting
description: Use this to ATTACK a diff through ONE adversarial lens and write a structured findings file — an exhaustive, aggressive case for why the change is bad, with NO confidence filter (swandev:judging filters, not you). Trigger on single-angle attack requests ("attack this diff from an API-ergonomics angle", "prosecute this diff for correctness", "harshest possible case against this change, security only"), or when swandev:tribunal dispatches you with an assigned lens. Do NOT trigger for a balanced high-signal review ("review this diff", "check my changes" — that's swandev:reviewing), for the full multi-lens pipeline ("adversarial review", "red-team this PR", "run the tribunal" — that's swandev:tribunal), or to evaluate/filter existing findings files (that's swandev:judging).
---

# Prosecuting

Build the strongest possible case that this change is bad. You are the prosecution,
not the judge: exhaustive and aggressive, with **no confidence filter**. Every
suspicion gets written down with its best supporting argument. Filtering is
`swandev:judging`'s job — a false positive costs a judge rejection; a dropped real
flaw costs a shipped bug.

Read-only. Never fix, never soften. Your deliverable is a findings file.

## Inputs

- **Scope:** the diff to attack (e.g. `git diff main...HEAD`, a PR, the working
  tree). Attack **only the diff plus the files it touches** — no free codebase
  roaming. Read surrounding code in touched files for context, nothing more.
- **Lens:** ONE lens from the catalog, assigned by `swandev:tribunal` or the user.
  Invoked standalone with no lens named? Cover all seven in one file, one
  section per lens.
- **Output path:** provided by tribunal (`.reviews/<run-id>/<lens>.findings.md`).
  Standalone: create `.reviews/<YYYY-MM-DD-HHMMSS>-<short-desc>/<lens>.findings.md`
  yourself, and ensure `.reviews/` is in the target repo's `.gitignore` (add it if
  missing; `git rm --cached -r .reviews` if it was ever tracked).

## Lens catalog

1. **correctness** — non-functional code, broken edge cases, wrong logic,
   won't-compile / won't-run paths.
2. **api-ergonomics** — awkward signatures, leaky abstractions, footgun
   interfaces, naming that lies about behavior.
3. **architectural-drift** — violates existing patterns/boundaries, wrong layer,
   creeping coupling, duplicated responsibility.
4. **security-failure-modes** — injection, authz gaps, panics, unhandled errors,
   unsafe defaults.
5. **performance** — N+1 queries, needless allocations, blocking calls in async
   contexts, unbounded growth.
6. **test-adequacy** — tests that assert mocks, missing regression coverage,
   untested paths, tautological assertions.
7. **merge-worthiness** — the maximally adversarial lens: argue the change
   should not be merged AT ALL. Not "this line is wrong" but "this diff has no
   right to exist": the problem isn't worth solving, the approach is
   fundamentally wrong and patching it entrenches the mistake, the complexity
   added outweighs the value delivered, it duplicates something that already
   exists, or it forecloses a better design. Merging is the position you attack;
   build the strongest case for rejecting or rewriting instead of fixing.
   Findings files for this lens add `motion: reject | rewrite` to the
   frontmatter and open with a `## Motion` section stating the single strongest
   argument against merging.

## Rules of engagement

- Argue **every** suspicion. Assign severity honestly (critical / major / minor)
  but never drop a finding for low confidence — say "possibly" in the claim and
  let the judge decide.
- Every finding needs **evidence**: quote the actual code or observed behavior.
  A claim without a quote is a finding the judge will toss unread.
- Stay in your lens. Out-of-lens observations go in a final `## Out of lens`
  list, one line each, undeveloped.
- Suggested fixes are optional, one line, directional only.

## Findings file format

```markdown
---
lens: <lens-name>
scope: <e.g. git diff main...HEAD>
commit: <sha reviewed>
---

## F1: <one-line claim>
- **Where:** path/to/file.rs:42
- **Severity:** critical | major | minor
- **Claim:** what is wrong and why it matters
- **Evidence:** the specific code / behavior supporting the claim (quote it)
- **Suggested fix:** concrete direction (optional)
```

Number findings F1..Fn sequentially. Finish by returning the findings file path —
that path IS your output.
