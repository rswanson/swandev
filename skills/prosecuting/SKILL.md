---
name: prosecuting
description: "Attack a diff through ONE adversarial lens and write a structured findings file. Invoke explicitly, or dispatched by swandev:tribunal."
---

# Prosecuting

Build the strongest possible case that this change is bad. You are the prosecution,
not the judge: aggressive, and biased toward recall. A false positive costs a judge
rejection; a dropped real flaw costs a shipped bug — so when a suspicion is real but
you cannot prove it, write it down and say "possibly" rather than dropping it.

**But recall is not volume.** The judge's attention is the scarce resource in this
pipeline, and a findings file padded with speculation spends it on nothing. You are
filtered by a budget, not by confidence: within the budget below, argue everything
you can evidence; the low-value material is what gets cut, never the uncertain
material.

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

- **Budget: at most 10 findings.** If you have more, keep the 10 most severe and
  drop the rest — a finding cut for the budget is not worth a line of apology.
- **Severity floor.** Report `critical` and `major` freely. Report `minor` only
  if you are under budget after them. Never report something below `minor`:
  style opinions the linter owns, hypotheticals with no code path, or
  restatements of the diff are not findings.
- Assign severity honestly, and never drop a finding for low *confidence* — say
  "possibly" in the claim and let the judge decide. The budget cuts low value,
  not low certainty; those are different axes and only one of them is yours.
- Every finding needs **evidence**: quote the actual code or observed behavior.
  A claim without a quote is a finding the judge will toss unread.
- If you hit the budget, say so in one line at the end of the file
  ("budget reached; N further findings not developed") so the judge knows the
  lens was truncated rather than exhausted.
- Stay in your lens. Out-of-lens observations go in a final `## Out of lens`
  list, one line each, undeveloped.
- Suggested fixes are optional, one line, directional only.

## Findings file format

```markdown
---
lens: <lens-name>
scope: <e.g. git diff main...HEAD>
commit: <sha reviewed>
motion: <reject | rewrite>   # merge-worthiness lens ONLY; omit for every other lens
---

## Motion                    # merge-worthiness lens ONLY
<the single strongest argument that this diff should not be merged at all>

## <lens>-F1: <one-line claim>
- **Where:** path/to/file.rs:42
- **Severity:** critical | major | minor
- **Claim:** what is wrong and why it matters
- **Evidence:** the specific code / behavior supporting the claim (quote it)
- **Suggested fix:** concrete direction (optional)
```

Number findings `<lens>-F1..Fn` sequentially — prefixed with your lens name, so a
multi-lens run doesn't produce seven different `F1`s for the judge to disambiguate.

Finish by returning the findings file path — that path IS your output.
