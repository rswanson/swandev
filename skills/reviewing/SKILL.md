---
name: reviewing
description: "Read-only two-stage review of a diff or task: spec compliance first, then code quality. Invoke explicitly. Produces a verdict, not a fix."
---

# Reviewing

Assess a diff, branch, PR, or just-completed task against its requirements and for code quality. Read-only — produce a verdict, don't write the fix.

## Two stages (in order)

Run spec-compliance FIRST. Only if it passes, run code-quality — a change that built the wrong thing isn't worth a quality pass yet.

### Stage 1 — Spec compliance

Read the ACTUAL code; do not trust the implementer's summary.

- **Missing:** requirements not implemented.
- **Extra:** unrequested features, over-engineering, scope creep.
- **Misunderstood:** right feature, wrong interpretation.

Report ✅ compliant, or ❌ with specific `file:line` references. If ❌, stop — the implementer fixes, then re-review stage 1.

### Stage 2 — Code quality (only after stage 1 ✅)

- Correctness / bugs / edge cases.
- Security.
- Clarity & naming (names match what things do, not how).
- Test quality — tests verify behavior, not mocks; a bugfix has a regression test that fails before and passes after.
- Conventions & file responsibility (one clear purpose; not over-grown).
- Project checks were actually run: the repo's formatter, linter, and test suite (or its Makefile/CI-defined equivalents). Flag if they weren't.

Report **Strengths**, then **Issues** as Critical / Important / Minor (each with `file:line` and the fix), then a one-line **Assessment**.

## Confidence filter

Report high-signal issues only. Don't pad with nitpicks or style opinions the linters already own. If you're unsure an issue is real, say so or leave it out.

## Scope & inputs

Establish what you're reviewing (task commits, working tree, or a branch range — e.g. `git diff main...HEAD`) and the requirements it should meet (the task or spec). Review only that diff, not the whole codebase.

## Loop & boundary

Issues → implementer fixes → re-review until clean. This skill ASSESSES; it does not write the fix (that's `swandev:tdd`), diagnose a live crash/failure (that's `swandev:debugging`), or run final CI and open/merge the PR (that's `swandev:pr`). `swandev:executing` invokes this per task; it's also invoked standalone for any "review this".

A change that took the `swandev:tdd` **fast path** (genuinely atomic — typo, config value, dep bump) does not need a separate dispatch here; the inline self-review there suffices. Still invoke this standalone whenever the user explicitly asks for a review, regardless of size.
