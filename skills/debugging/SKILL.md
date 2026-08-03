---
name: debugging
description: Use this when code that is supposed to already work exhibits an UNEXPECTED, OBSERVED defect — a bug, crash, panic, wrong output, regression, or a test/CI failure you cannot explain — BEFORE proposing or attempting a fix, even when the user already proposes a fix ("just add a nil-check"). Trigger when the user says "this is failing", "why does this break", "it panics", "the test won't pass", "unexpected behavior", or pastes an error or stack trace. EXCLUDES expected failures during a batch's acceptance-test red step (a test just written for behavior that does not exist yet), compile/undefined-symbol errors from not-yet-written code, and merely writing new error-handling/error-branch code — those belong to swandev:implementing. If a crash/panic/wrong-output is happening NOW, run this FIRST to confirm root cause, then hand the red→green regression cycle back to the swandev:implementing loop. If the user already has a fix in hand and only wants to push/ship/merge it, that is swandev:implementing's ship step, not debugging.
---

# Systematic Debugging

## The iron law

NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST. A symptom fix is a failure. This holds especially under time pressure and when "one quick fix" looks obvious.

## Phase 1 — Investigate (before ANY fix)

1. **Read the error fully** — stack trace, line numbers, file paths, error codes. The message often contains the answer.
2. **Reproduce consistently** — exact steps; does it happen every time? If not reproducible, gather more data — do not guess.
3. **Check recent changes** — `git diff`, recent commits, new deps, config/env differences.
4. **Identify the responsible component first** — for auth/RPC/networking, trace the request path explicitly before assuming which service is at fault. Read configs for ALL related components (prod + dev, both sides of a boundary) before forming a diagnosis.
5. **Instrument multi-component boundaries** — log what data enters and exits each component to localize where reality diverges from expectation.

State a hypothesis grounded in evidence before touching code.

## Phase 2 — Fix the root cause

- Address the cause the evidence points to, not the symptom.
- A bugfix ALWAYS gets a regression test FIRST — write it (or hand the red→green cycle to a `swandev:implementing` fix pass), confirm it fails before the fix and passes after. Do NOT close out the bug without this test.
- For flag/env-gated paths, confirm BOTH that the code path is enabled AND that all required config is set (including empty-string defaults).

## Phase 3 — Verify

- Reproduce the original trigger; confirm it's gone.
- Run the project's formatter, linter, and test suite (e.g. `cargo fmt`/`clippy`/`test` for Rust, `go vet`/`go test` for Go, a dry-run/preview for IaC).
- Confirm no new failures introduced.

## When you're stuck

Keep instrumenting the suspected boundary and narrow with bisection — use `git bisect` to locate which commit introduced a regression when `git diff`/recent commits are inconclusive. State the remaining hypotheses to the user before any speculative change. Never downgrade to a symptom patch just because the root cause is elusive.

## Production issues

Start with the simplest hypothesis matching the evidence. Ask for logs and metrics first; don't suggest resource increases or probe changes without data.
