---
name: specifying
description: Use this BEFORE any code or batch plan exists, to turn an idea into a high-detail, assumption-free spec through relentless user questioning — deciding WHAT to build and pinning every detail. Trigger when the user says "let's build/design X", "I want to add", "spec this out", "I'm thinking about", "help me figure out", "flesh this out", or describes something to create with no approved spec. NEVER make large assumptions — every unknown becomes an assumption-ledger entry only the user can resolve. If an approved spec already exists and needs slicing into deployable batches, defer to swandev:batching; if an approved batch plan exists and the user wants to build, that's swandev:implementing; an observed defect in existing code is swandev:debugging. Writes no code, scaffolds nothing.
---

# Specifying

Turn an idea into a spec detailed enough to slice into deployable batches.
Extract maximum user input; assume nothing you can ask instead.

## Hard gates

- Do NOT write code, scaffold, or invoke `swandev:batching` until the user
  approves the spec.
- The spec CANNOT be approved while any assumption-ledger entry is unresolved.
- About to write "probably", "presumably", "we can assume", or silently pick
  between two plausible readings? STOP — that is a ledger entry, not prose.

## Process

1. **Explore first** — read relevant files, docs, and recent commits before
   asking anything. Never ask what the repo already answers.
2. **Scope check** — if the request spans multiple independent subsystems,
   decompose into sub-projects; each gets its own spec → batches → build cycle.
3. **Interview, one question at a time** — AskUserQuestion, multiple-choice
   with your recommendation first when possible. Never batch questions. Cover:
   purpose, users, constraints, interfaces, data, edge cases, failure modes,
   success criteria.
4. **Build the spec section by section**, in order: Goals & non-goals → Users &
   flows → Scope boundaries → Behavior (interfaces, data, commands) → Edge
   cases & failure modes → Testing & acceptance. Present each section and get
   explicit approval before drafting the next.
5. **Maintain the assumption ledger** throughout — a table in the spec doc:

   ```markdown
   | # | Question | Proposed default | Status |
   |---|----------|------------------|--------|
   | 1 | Should deletes cascade? | No — reject with 409 | OPEN |
   ```

   An entry resolves ONLY when the user answers it or explicitly confirms the
   proposed default (record which). Sweep the ledger with AskUserQuestion as
   entries accumulate; resolved entries move to a Decision Log section.
6. **Write the spec** to `docs/specs/YYYY-MM-DD-<topic>-spec.md`. Create a git
   worktree FIRST (never edit on main — confirm with `git worktree list` and
   `git branch --show-current`). Commit as DRAFT.
7. **Self-review** — scan for placeholders, contradictions, scope creep, and
   any "probably/presumably/assume" language that escaped the ledger. Fix
   inline.
8. **Approval gate** — present the spec. If any ledger entry is OPEN, the only
   valid outcomes are answers to those entries; do not accept approval over an
   open entry. Make requested changes and re-review.
9. **Hand off** — invoke `swandev:batching`. That is the ONLY skill you invoke
   next.

## Spec document skeleton

```markdown
# <topic> — spec

Status: DRAFT | APPROVED
Date: YYYY-MM-DD

## Goals / Non-goals
## Users & flows
## Scope boundaries
## Behavior (interfaces, data, commands)
## Edge cases & failure modes
## Testing & acceptance
## Assumption ledger   <- must be empty of OPEN entries at approval
## Decision log        <- every resolved entry, with who/what resolved it
```

## Principles

- One question at a time; multiple choice when possible; recommendation first.
- YAGNI — cut features the user hasn't asked for from every draft.
- Prefer the user's words over your paraphrase for requirements.
- In existing codebases, follow established patterns; don't propose unrelated
  refactors.
