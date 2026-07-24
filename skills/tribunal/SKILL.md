---
name: tribunal
description: "Full adversarial review pipeline: parallel single-lens prosecutors, then one verifying judge. Heavyweight and expensive; invoke explicitly only."
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

Every lens is an agent plus a share of the judge's attention, so the default is
deliberately narrow. **Default set (four):** correctness, security-failure-modes,
architectural-drift, test-adequacy.

Add a lens only when the diff earns it:

- **api-ergonomics** — the diff changes a public interface, a signature, or
  anything another caller binds to.
- **performance** — hot paths, queries, loops over unbounded input, async code.
- **merge-worthiness** — the change is large, novel, or its *approach* (rather
  than its execution) is genuinely in question. Do NOT run it on a diff whose
  right to exist isn't in doubt: a one-line config fix does not need an agent
  arguing it should never have been written.

"Run all seven" is a valid explicit request — honour it when asked. Otherwise
state in one line which lenses you selected and why.

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
// only the lenses you selected in step 2
const LENSES = [
  { lens: 'correctness', model: 'sonnet' },
  { lens: 'security-failure-modes', model: 'sonnet' },
  { lens: 'test-adequacy', model: 'sonnet' },
  { lens: 'architectural-drift' },
]
phase('Prosecute')
const paths = await parallel(LENSES.map(l => () =>
  agent(
    `Invoke the Skill tool with skill "swandev:prosecuting" and follow it exactly. ` +
    `Lens: ${l.lens}. Scope: ${args.scope}. ` +
    `Requirements context: ${args.spec || 'NONE PROVIDED — say so in your findings file ' +
      'and do not infer intent you cannot evidence.'} ` +
    `Write your findings file to ${args.runDir}/${l.lens}.findings.md and return that path.`,
    { label: `prosecute:${l.lens}`, ...(l.model ? { model: l.model } : {}) }
  )))
return { paths }
```

Pass `args: { scope, runDir, spec }` in the Workflow call. **`spec` is the
requirements context from step 1** — the spec text, task description, or PR
body, inlined (not a path an agent has to go find). Without it the
intent-dependent lenses are guessing: test-adequacy cannot judge missing
coverage against no requirement, and correctness cannot tell a bug from an
intended behaviour change. If there genuinely is no requirements context, pass
nothing and let the fallback clause fire.

Prosecutors get the diff plus touched files only — bounded scope is a cost
lever, restate it in the prompt if the diff is large.

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
