---
name: pr
description: Create a pull request with local CI validation. Use this skill whenever the user wants to create a PR, open a pull request, submit their work for review, push and create a PR, or says "/pr". Also use when the user says things like "I'm done, let's get this merged", "ship it", "ready for review", or "create a PR for this".
---

# PR Creation Skill

Catch CI failures locally before pushing, then create a well-formatted PR following project conventions.

## Step 1: Verify Worktree Context

Run `git worktree list` and verify the current directory is a worktree, not the main working tree. If not in a worktree, stop and tell the user — PRs must be created from a worktree.

## Step 2: Analyze Changes

1. Run `git log main..HEAD --oneline` for committed changes
2. Run `git status` and `git diff` for uncommitted work
3. Run `git diff main...HEAD --name-only` to determine which checks to run

## Step 3: Handle Uncommitted Work

If uncommitted changes exist, assess whether they're related to the branch's work:
- **Related**: Stage specific files and commit (imperative mood, include `Co-Authored-By` line)
- **Unrelated**: Stop and ask the user — don't mix unrelated changes into the PR

## Step 4: Run Local CI Checks

Infer which checks to run from the changed paths (`git diff main...HEAD --name-only`) and the project's stack. Run independent checks in parallel. If any check fails, stop and help fix before proceeding — never push code that hasn't passed.

Prefer whatever the repo itself defines when present (Makefile targets, `package.json`/`justfile` scripts, pre-commit hooks, the CI workflow's own steps) over guessing. Otherwise run the stack's canonical checks for the changed paths — formatter, linter, build, and tests (e.g. `cargo fmt --check` / `cargo clippy` / `cargo test` for Rust, `go build` / `go vet` / `go test ./...` for Go), plus a dry-run/preview for IaC changes. If a required tool or credential isn't available locally, note it and proceed — CI covers it after push. If you can't tell which checks apply, ask rather than skip them.

## Step 5: Push and Create PR

Push with `git push -u origin HEAD` (or `git push` if upstream exists). Then create the PR with `gh pr create`. Base branch defaults to `main` — ask the user if ambiguous. Don't use `--draft` unless requested.

### Title format

Conventional commit style, under 70 chars, lowercase imperative: `type: description`

Types: `feat:` (new functionality), `fix:` (bug fix), `config:` (config/routing changes), `ci:` (CI/CD), `chore:` (maintenance), `docs:` (documentation)

### Body format

```markdown
## Summary
- [1-3 bullet points describing what changed and why]

## Details (optional — only for complex changes)
[Technical context, design decisions]

## Test plan
- [x] Local checks that passed
- [ ] Post-deploy verification steps

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

After creation, report the PR URL and which CI workflows should trigger based on the changed paths.
