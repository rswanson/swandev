---
name: brainstorming
description: Use this BEFORE any creative work when no approved design/spec exists yet — deciding WHAT to build, WHETHER to build it, or the right approach/architecture/structure: designing a feature, adding functionality, building a component, changing behavior, choosing an architecture, or starting a new project. Trigger when the user says "let's build/design X", "I want to add", "I'm thinking about", "help me figure out", "what's the best way to", "how should we approach", "what would X look like", or describes something to create even without explicitly asking for a design. The idea→spec step; hand off to swandev:planning once a spec is approved. If the user already knows what to build and only wants tasks/steps/a breakdown, defer to swandev:planning; if they give a direct imperative to build a specific, clearly-scoped change (not an open-ended idea), defer to swandev:tdd. Don't write code or scaffold until a design is approved.
---

# Brainstorming

Turn ideas into approved designs through collaborative dialogue. Understand intent before proposing anything.

## Hard gate

Do NOT write code, scaffold, or invoke an implementation skill until you have presented a design and the user has approved it. Every project goes through this — "too simple to design" is the trap that wastes the most work. A simple design can be three sentences; you still present it and get approval.

Exception: if an approved design/spec already exists, or the user already knows what to build and is only asking for a task/step breakdown, do NOT run the design dialogue — hand directly to `swandev:planning`. This gate is about deciding WHAT/WHETHER to build, not about blocking execution of already-decided work.

## Process

1. **Explore context** — read relevant files, docs, recent commits before asking anything.
2. **Scope check** — if the request spans multiple independent subsystems, say so and help decompose into sub-projects before diving in. Each sub-project gets its own spec → plan → build cycle.
3. **Ask one question at a time** — purpose, constraints, success criteria. Prefer multiple-choice. Never batch questions.
4. **Propose 2–3 approaches** — with trade-offs; lead with your recommendation and why.
5. **Present the design in sections** — scaled to complexity. Get approval after each section. Cover architecture, components, data flow, error handling, testing.
6. **Write the spec** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md`. Create a git worktree FIRST (never edit on main) so nothing untracked lands on the main branch — confirm with `git worktree list`. Commit it as a DRAFT spec under review (approval at step 8 may produce follow-up commits).
7. **Self-review the spec** — scan for placeholders, contradictions, ambiguity, scope creep. Fix inline.
8. **User reviews the spec** — wait for approval. Make requested changes and re-review.
9. **Hand off** — invoke `swandev:planning`. That is the ONLY skill you invoke next.

## Principles

- One question at a time. Multiple choice when possible.
- YAGNI — cut unnecessary features from every design.
- Always explore alternatives before settling.
- Design in small units with clear boundaries: each should have one purpose, a defined interface, and be understandable on its own.
- In existing codebases, explore structure first and follow established patterns. Improve code you're working in where it serves the goal; don't propose unrelated refactors.
- Be flexible — go back and re-clarify when something doesn't fit.
