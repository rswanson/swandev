---
name: judging
description: Use this to JUDGE adversarial-review findings files (produced by swandev:prosecuting) — dedup them, VERIFY every claim against the actual code, score validity × value, write a verdict file, present accepted findings for USER APPROVAL, then dispatch the approved fixes to Sonnet implementer subagents. Trigger when the user points at findings file(s) ("judge these findings", "which of these findings are real", "score the findings in .reviews/ and fix the good ones"), or when swandev:tribunal hands over a run directory. Do NOT trigger to GENERATE findings (that's swandev:prosecuting for one lens, swandev:tribunal for the full pipeline), or for a normal review of a diff with no findings files involved (that's swandev:reviewing).
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
   code yourself.
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

## F3 (correctness, security): <merged one-line claim>
- **Verdict:** accepted | rejected | duplicate-of F1
- **Verification:** what you read in the code and what it showed
- **Validity/Value:** high/medium/low × high/medium/low
- **Where:** path/to/file.rs:42
- **Fix direction:** one line (accepted findings only)
```

5. **Present** the accepted findings to the user, ranked by validity × value,
   each with a one-line rationale. Then the gate.

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
- If parallel groups conflict on merge, the grouping was wrong — stop and
  re-group (same rule as swandev:executing).

## Malformed input

Salvage what parses; anything unparseable is quoted verbatim in the verdict file
under `## Unparsed` and mentioned to the user — never silently dropped.
