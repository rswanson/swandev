---
name: debugging
description: "Root-cause-first investigation of an observed defect before any fix is attempted. Invoke explicitly, when something that should already work is failing."
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
- A bugfix ALWAYS gets a regression test FIRST — write it (or hand the red→green cycle to `swandev:tdd`), confirm it fails before the fix and passes after. Do NOT close out the bug without this test.
- For flag/env-gated paths, confirm BOTH that the code path is enabled AND that all required config is set (including empty-string defaults).

## Phase 3 — Verify

- Reproduce the original trigger; confirm it's gone.
- Run the project's formatter, linter, and test suite (e.g. `cargo fmt`/`clippy`/`test` for Rust, `go vet`/`go test` for Go, a dry-run/preview for IaC).
- Confirm no new failures introduced.

## When you're stuck

Keep instrumenting the suspected boundary and narrow with bisection — use `git bisect` to locate which commit introduced a regression when `git diff`/recent commits are inconclusive. State the remaining hypotheses to the user before any speculative change. Never downgrade to a symptom patch just because the root cause is elusive.

## Production issues

Start with the simplest hypothesis matching the evidence. Ask for logs and metrics first; don't suggest resource increases or probe changes without data.
