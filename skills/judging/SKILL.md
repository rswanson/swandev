---
name: judging
description: "Verify, score, and user-gate adversarial findings files, then dispatch and integrate approved fixes. Invoke explicitly, or handed over by swandev:tribunal."
---

# Judging

Findings files are accusations, not facts. Your job: verify each against the real
code, keep what holds and matters, discard the rest with reasons, and — only after
the user approves — dispatch fixes.

Run in the main conversation (not a subagent): the user-approval gate needs
interactivity.

## Inputs

- One or more findings file paths (usually a `.reviews/<run-id>/` directory of
  `<lens>.findings.md` files) and the diff scope they reviewed.
- If tribunal reported missing lenses (dead prosecutor), note the coverage gap in
  the verdict and in your summary to the user.

## Process

1. **Dedup.** Findings from different lenses hitting the same file/line/claim
   merge into one, recording every lens that flagged it — multi-lens hits are a
   strong prior that it's real.
2. **Verify.** For each deduped finding, read the actual code and classify:
   - **holds** — the code does what the claim says;
   - **mis-states** — partially right; record the corrected claim;
   - **refuted** — the code contradicts the claim; record why.
   A prosecutor's quote is a pointer, not proof — always read the surrounding
   code yourself. Where a claim is decidable by running something — won't
   compile, test doesn't cover it, the repro fails — RUN it and record the
   command and its output in the Verification field. An executed check outranks
   any amount of reading.
3. **Score.** For findings that hold (or mis-state but still matter):
   validity (does it hold as stated?) × value (is fixing it worth the change?),
   each high/medium/low. Accept only findings worth acting on; everything else
   is rejected **with the reason kept** — the audit trail is part of the output.
4. **Write the verdict file** to `<run-dir>/verdict.md`:

```markdown
---
scope: <diff scope>
findings-files: [<paths>]
missing-lenses: [<any lenses tribunal reported dead>]
---

## correctness-F3 (also: security-F1): <merged one-line claim>
- **Verdict:** accepted | rejected | duplicate-of <lens>-F1
- **Verification:** what you read in the code and what it showed
- **Validity/Value:** high/medium/low × high/medium/low
- **Where:** path/to/file.rs:42
- **Fix direction:** one line (accepted findings only)
```

5. **Present** the accepted findings to the user, ranked by validity × value,
   each with a one-line rationale. **Cap the list at 8.** If more than 8 were
   accepted, present the top 8 and summarise the remainder as one line —
   "N further accepted findings recorded in the verdict file, not dispatched" —
   naming the file. The cap is on what you ASK about, never on what you verify
   or record. Then the gate.

**Motions.** A merge-worthiness findings file carries a `motion: reject | rewrite`
against the whole diff. Verify its argument like any finding, but it is never
dispatched as a fix: if it holds, record it at the top of the verdict file as
`motion: <reject|rewrite> — sustained | overruled (<reason>)` and lead your
summary to the user with it — whether to merge at all is the user's call and
comes before any per-finding fixes.

## User gate (hard)

Nothing is dispatched without explicit approval. Use AskUserQuestion (multiSelect)
listing the accepted findings; the user picks which to fix. "Fix all" and
"fix none / report only" are always available outcomes.

## Dispatch

- Group approved findings by **disjoint file sets** — findings touching the same
  file go in one group.
- One Sonnet implementer per group: `Agent` tool, `model: sonnet`,
  `isolation: 'worktree'` whenever more than one group runs in parallel.
- Lean fix prompt per group (do NOT invoke swandev:tdd — findings are narrow):

```text
Fix the following verified code-review finding(s) in <worktree/branch>.

<for each finding: the verdict.md block — claim, where, verification note, fix direction>

House rules:
- A bug-class fix gets a regression test that fails before and passes after.
- Run the project's formatter, linter, and test suite before you finish.
- One commit per finding, message referencing the finding id.
- Fix ONLY these findings; no drive-by refactors.
```

- **Verify each fix** yourself: does the change actually address the finding?
  If not, one re-dispatch with what was wrong; after that, report it unresolved
  with the failure output. No silent retry loops.
- **Integrate.** Merge each group's branch back into the branch under review, one
  at a time, then run the project's checks once on the integrated result. A
  finding is NOT resolved until its commit is on that branch — fixes left sitting
  in a worktree are the same as no fix at all. Report the commit shas.
- If parallel groups conflict on merge, the grouping was wrong — stop and
  re-group (same rule as swandev:executing).
- Control returns to whoever invoked you. Do not open or merge a PR.

## Malformed input

Salvage what parses; anything unparseable is quoted verbatim in the verdict file
under `## Unparsed` and mentioned to the user — never silently dropped.
