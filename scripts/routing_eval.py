#!/usr/bin/env python3
"""Tier 2 routing-accuracy eval for the swandev plugin repo.

Stdlib only. Builds one routing prompt from every skills/*/SKILL.md
frontmatter description, runs every evals/*.eval.json case against
`claude -p --model claude-haiku-4-5` in a fresh, project-free temp
directory, scores the replies, prints a per-skill table, writes
eval-results.json, and exits non-zero if the accuracy floors are not met.

Usage: python3 scripts/routing_eval.py [--limit N]   (run from repo root)
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL = "claude-haiku-4-5"
MAX_WORKERS = 8
TIMEOUT_SECONDS = 120

OVERALL_FLOOR = 90.0
PER_SKILL_FLOOR = 80.0

FRONTMATTER_RE = re.compile(
    r"^---\nname: (?P<name>[^\n]+)\ndescription: (?P<description>[^\n]+)\n---\n"
)


def load_skills():
    """Return an ordered list of (name, description) from skills/*/SKILL.md."""
    skills = []
    for path in sorted(glob.glob(os.path.join(REPO_ROOT, "skills", "*", "SKILL.md"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        m = FRONTMATTER_RE.match(text)
        if not m:
            print(f"routing_eval: skipping {path}: malformed frontmatter", file=sys.stderr)
            continue
        skills.append((m.group("name"), m.group("description")))
    return skills


def build_template(skills):
    """One shared routing prompt template listing every skill."""
    skill_lines = "\n".join(f"- {name}: {description}" for name, description in skills)
    return (
        "You are a routing assistant for a Claude Code plugin. Below is the "
        "full list of available skills, each with a description of when it "
        "should be used.\n\n"
        f"{skill_lines}\n\n"
        "Given the user query below, reply with ONLY the single best-matching "
        "skill name from the list above, or the word \"none\" if no skill "
        "should trigger. No punctuation, no explanation — the skill name (or "
        "\"none\") and nothing else.\n\n"
        "User query: "
    )


def load_cases():
    """Flatten every evals/<skill>.eval.json into (skill, query, should_trigger)."""
    cases = []
    for path in sorted(glob.glob(os.path.join(REPO_ROOT, "evals", "*.eval.json"))):
        skill = os.path.basename(path)[: -len(".eval.json")]
        with open(path, encoding="utf-8") as f:
            entries = json.load(f)
        for entry in entries:
            cases.append(
                {
                    "skill": skill,
                    "query": entry["query"],
                    "should_trigger": entry["should_trigger"],
                }
            )
    return cases


def normalize_reply(raw):
    """Strip whitespace/quotes/backticks/trailing periods, lowercase."""
    s = raw.strip()
    s = s.strip(" \t\r\n`'\"")
    s = s.rstrip(".")
    s = s.strip(" \t\r\n`'\"")
    return s.lower()


def call_claude(prompt):
    """Run `claude -p --model MODEL <prompt>` in a fresh temp dir.

    Returns (ok, raw_output) where raw_output is stdout on success, or a
    marker string describing the failure (timeout / non-zero exit / spawn
    error) on failure.
    """
    tmpdir = tempfile.mkdtemp(prefix="routing_eval_")
    try:
        proc = subprocess.run(
            ["claude", "-p", "--model", MODEL, prompt],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, "<timeout>"
    except OSError as exc:
        return False, f"<spawn error: {exc}>"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return False, f"<exit {proc.returncode}: {detail[:200]}>"

    return True, proc.stdout


def run_case(template, case, valid_replies):
    prompt = template + case["query"]
    ok, raw = call_claude(prompt)

    reply_for_matching = normalize_reply(raw) if ok else None
    is_well_formed = ok and reply_for_matching in valid_replies

    if is_well_formed:
        if case["should_trigger"]:
            correct = reply_for_matching == case["skill"]
        else:
            correct = reply_for_matching != case["skill"]
        recorded_reply = reply_for_matching
    else:
        correct = False
        recorded_reply = raw.strip() if ok else raw

    return {
        "skill": case["skill"],
        "query": case["query"],
        "should_trigger": case["should_trigger"],
        "reply": recorded_reply,
        "correct": correct,
    }


def print_table(results):
    by_skill = {}
    for r in results:
        stats = by_skill.setdefault(
            r["skill"], {"cases": 0, "correct": 0, "missed": 0, "false": 0}
        )
        stats["cases"] += 1
        if r["correct"]:
            stats["correct"] += 1
        elif r["should_trigger"]:
            stats["missed"] += 1
        else:
            stats["false"] += 1

    header = f"{'skill':<14}{'cases':>7}{'correct':>9}{'accuracy%':>11}{'missed-triggers':>18}{'false-triggers':>16}"
    print(header)
    print("-" * len(header))

    per_skill_accuracy = {}
    for skill in sorted(by_skill):
        s = by_skill[skill]
        accuracy = (s["correct"] / s["cases"] * 100) if s["cases"] else 0.0
        per_skill_accuracy[skill] = accuracy
        print(
            f"{skill:<14}{s['cases']:>7}{s['correct']:>9}{accuracy:>10.1f}%"
            f"{s['missed']:>18}{s['false']:>16}"
        )

    total_cases = len(results)
    total_correct = sum(1 for r in results if r["correct"])
    overall_accuracy = (total_correct / total_cases * 100) if total_cases else 0.0

    print()
    print(f"overall: {total_correct}/{total_cases} correct ({overall_accuracy:.1f}%)")

    return overall_accuracy, per_skill_accuracy


def main():
    parser = argparse.ArgumentParser(description="Tier 2 routing-accuracy eval")
    parser.add_argument(
        "--limit", type=int, default=None, help="run only the first N cases (smoke test)"
    )
    args = parser.parse_args()

    skills = load_skills()
    if not skills:
        print("routing_eval: no skills found under skills/*/SKILL.md", file=sys.stderr)
        return 1
    skill_names = {name for name, _ in skills}
    valid_replies = skill_names | {"none"}

    template = build_template(skills)
    cases = load_cases()
    if args.limit is not None:
        cases = cases[: args.limit]

    if not cases:
        print("routing_eval: no eval cases to run", file=sys.stderr)
        return 1

    results = [None] * len(cases)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(run_case, template, case, valid_replies): i
            for i, case in enumerate(cases)
        }
        for future in futures:
            i = futures[future]
            results[i] = future.result()

    out_path = os.path.join(REPO_ROOT, "eval-results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    overall_accuracy, per_skill_accuracy = print_table(results)

    failures = []
    if overall_accuracy < OVERALL_FLOOR:
        failures.append(f"overall accuracy {overall_accuracy:.1f}% < {OVERALL_FLOOR:.0f}% floor")
    for skill, accuracy in sorted(per_skill_accuracy.items()):
        if accuracy < PER_SKILL_FLOOR:
            failures.append(f"{skill} accuracy {accuracy:.1f}% < {PER_SKILL_FLOOR:.0f}% floor")

    print()
    if failures:
        print("routing_eval: FAILED")
        for msg in failures:
            print(f"    {msg}")
        return 1

    print("routing_eval: all floors passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
