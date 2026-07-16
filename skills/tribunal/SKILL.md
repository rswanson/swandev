---
name: tribunal
description: Use this to run a FULL ADVERSARIAL REVIEW PIPELINE on a diff/branch/PR — fan out parallel single-lens swandev:prosecuting agents (correctness, API ergonomics, architectural drift, security, performance, test adequacy, merge-worthiness), then hand all findings files to one swandev:judging pass (verify → user gate → dispatch fixes). This is the heavyweight, explicitly-invoked deep audit. Trigger on "adversarial review", "red-team this diff/PR", "tear this apart", "run the tribunal", "deep audit this change". Do NOT trigger for an ordinary review ("review this diff", "check my changes", "is this ready" — that's swandev:reviewing, the fast high-signal gate), for a single-lens attack (that's swandev:prosecuting), or when findings files already exist and only need judging (that's swandev:judging).
---

# Tribunal

Orchestrate the adversarial review pipeline: many prosecutors, one judge, user-gated
fixes. You do the scoping and fan-out; `swandev:prosecuting` does the attacking;
`swandev:judging` does everything from verdict onward.

## 1. Scope

- Establish the diff (`git diff main...HEAD`, a PR, or the working tree) and any
  requirements context (spec, task description) worth passing to reviewers.
- Create the run directory `.reviews/<YYYY-MM-DD-HHMMSS>-<short-desc>/` at the
  target repo root. Ensure `.reviews/` is gitignored (add it if missing;
  `git rm --cached -r .reviews` if it was ever tracked).

## 2. Select lenses

All seven by default: correctness, api-ergonomics, architectural-drift,
security-failure-modes, performance, test-adequacy, merge-worthiness. Drop only
obviously irrelevant ones (docs-only diff → drop test-adequacy and performance)
and TELL the user which were dropped and why. Never drop merge-worthiness —
every change defends its right to merge.

## 3. Fan out prosecutors (Workflow tool)

One `prosecuting` agent per lens, in parallel, with model tiering:

- **Sonnet** (`model: 'sonnet'`): correctness, security-failure-modes,
  performance, test-adequacy — recall-oriented lenses where the judge filters.
- **Session model** (omit `model`): architectural-drift, api-ergonomics,
  merge-worthiness — taste/judgment lenses where cheap models produce nitpicks
  that waste judge time. merge-worthiness especially: arguing a change has no
  right to exist takes holistic judgment, not pattern-matching.

Skeleton (adapt scope/run-dir; keep meta a pure literal):

```javascript
export const meta = {
  name: 'tribunal-fanout',
  description: 'Parallel single-lens adversarial reviewers',
  phases: [{ title: 'Prosecute' }],
}
const LENSES = [
  { lens: 'correctness', model: 'sonnet' },
  { lens: 'security-failure-modes', model: 'sonnet' },
  { lens: 'performance', model: 'sonnet' },
  { lens: 'test-adequacy', model: 'sonnet' },
  { lens: 'architectural-drift' },
  { lens: 'api-ergonomics' },
  { lens: 'merge-worthiness' },
]
phase('Prosecute')
const paths = await parallel(LENSES.map(l => () =>
  agent(
    `Invoke the Skill tool with skill "swandev:prosecuting" and follow it exactly. ` +
    `Lens: ${l.lens}. Scope: ${args.scope}. ` +
    `Write your findings file to ${args.runDir}/${l.lens}.findings.md and return that path.`,
    { label: `prosecute:${l.lens}`, ...(l.model ? { model: l.model } : {}) }
  )))
return { paths }
```

Pass `args: { scope, runDir }` in the Workflow call. Prosecutors get the diff plus
touched files only — bounded scope is a cost lever, restate it in the prompt if
the diff is large.

## 4. Handle casualties

A prosecutor that dies or returns nothing (null path / missing file) is a
**missing lens**, not a silent gap: list missing lenses in your summary and pass
them to the judge so the verdict records the coverage hole. Proceed regardless.

## 5. Judge

Invoke `swandev:judging` in the main conversation (NOT inside the workflow — the
user-approval gate needs interactivity) with the run directory, the scope, and
any missing lenses. The judge owns verify → verdict → user gate → dispatch.

## Boundary

`swandev:reviewing` remains the fast per-task gate inside swandev:executing; this
pipeline is never invoked automatically by the core loop — only explicitly.
