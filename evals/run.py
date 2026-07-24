#!/usr/bin/env python3
"""Routing eval runner for the swandev plugin.

Runs each case's prompt through a headless `claude` session with this plugin
loaded, and records which swandev skills the model actually invoked. A case
passes if the expected skill fired (`expect:`) or did not fire (`expect_not:`).

`claude plugin eval` is the official runner and would replace this, but it is
early-access gated at time of writing (it exits printing "`plugin eval` is
currently in early access" and runs nothing). The case files are laid out as
`evals/<skill>/case.yaml` to match its documented discovery pattern so the port
is mechanical once access opens.

Zero dependencies: stdlib only, so CI needs nothing but Python and the CLI.

  python3 evals/run.py --tag smoke          # cheap subset, ~16 cases
  python3 evals/run.py --skill reviewing    # one skill
  python3 evals/run.py                      # everything (slow, costs money)
"""

import argparse
import concurrent.futures as cf
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
SKILL_RE = re.compile(r"^swandev:[a-z]+$")


def parse_cases(path):
    """Parse the restricted YAML subset used by our case files.

    Supported: `skill: <v>`, `cases:` followed by `- prompt: "..."` blocks with
    `expect:`/`expect_not:`/`tags: [a, b]`. Anything else is a hard error rather
    than a silent skip -- a case file that does not parse must not look like a
    file with no cases.
    """
    cases, cur, in_cases = [], None, False
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.split("#", 1)[0].rstrip() if not raw.strip().startswith("#") else ""
        if not line.strip():
            continue
        if line.startswith("skill:"):
            continue
        if line.rstrip() == "cases:":
            in_cases = True
            continue
        if not in_cases:
            raise ValueError("%s:%d: unexpected line before `cases:`: %r" % (path, lineno, raw))

        m = re.match(r'\s*-\s+prompt:\s+"(.*)"\s*$', line)
        if m:
            if cur:
                cases.append(cur)
            cur = {"prompt": m.group(1).replace('\\"', '"').replace("\\\\", "\\"),
                   "tags": [], "expect": None, "expect_not": None, "line": lineno}
            continue
        if cur is None:
            raise ValueError("%s:%d: field outside a case: %r" % (path, lineno, raw))

        m = re.match(r"\s*expect:\s+(\S+)\s*$", line)
        if m:
            cur["expect"] = m.group(1)
            continue
        m = re.match(r"\s*expect_not:\s+(\S+)\s*$", line)
        if m:
            cur["expect_not"] = m.group(1)
            continue
        m = re.match(r"\s*tags:\s+\[(.*)\]\s*$", line)
        if m:
            cur["tags"] = [t.strip() for t in m.group(1).split(",") if t.strip()]
            continue
        raise ValueError("%s:%d: unrecognised line: %r" % (path, lineno, raw))

    if cur:
        cases.append(cur)

    for c in cases:
        if bool(c["expect"]) == bool(c["expect_not"]):
            raise ValueError("%s:%d: need exactly one of expect/expect_not" % (path, c["line"]))
        target = c["expect"] or c["expect_not"]
        if not SKILL_RE.match(target):
            raise ValueError("%s:%d: bad skill name %r" % (path, c["line"], target))
    return cases


def invoked_skills(prompt, plugin_dir, max_turns, model):
    """Run one prompt headless; return the list of swandev skills invoked."""
    cmd = [
        "claude", "-p", prompt,
        "--plugin-dir", str(plugin_dir),
        "--output-format", "stream-json", "--verbose",
        "--max-turns", str(max_turns),
    ]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return None, "timeout"

    skills = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "assistant":
            for c in d.get("message", {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Skill":
                    s = c.get("input", {}).get("skill")
                    if s:
                        skills.append(s)
    if not proc.stdout.strip():
        return None, (proc.stderr or "no output").strip()[:200]
    return skills, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", help="only cases from evals/<skill>/case.yaml")
    ap.add_argument("--tag", help="only cases carrying this tag")
    ap.add_argument("--plugin-dir", default=str(ROOT))
    ap.add_argument("--model", help="pass --model through to claude")
    ap.add_argument("--max-turns", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--threshold", type=float, default=1.0,
                    help="exit 1 if pass rate is below this (default 1.0)")
    ap.add_argument("--json", help="write full results to this path")
    ap.add_argument("--parse-only", action="store_true",
                    help="parse every case file and exit; runs nothing, costs nothing")
    args = ap.parse_args()

    files = sorted(EVALS.glob("*/case.yaml"))
    if args.skill:
        files = [f for f in files if f.parent.name == args.skill]
        if not files:
            sys.exit("no case file for skill %r" % args.skill)

    work = []
    total = 0
    for f in files:
        cases = parse_cases(f)          # raises on a malformed file
        total += len(cases)
        for c in cases:
            if args.tag and args.tag not in c["tags"]:
                continue
            work.append((f.parent.name, c))

    if args.parse_only:
        print("parsed %d cases across %d files — no cases run" % (total, len(files)))
        sys.exit(0)

    if not work:
        sys.exit("no cases matched")

    print("running %d cases across %d skills (jobs=%d)\n" % (
        len(work), len({w[0] for w in work}), args.jobs), flush=True)

    results = []

    def run_one(item):
        skill_dir, case = item
        skills, err = invoked_skills(case["prompt"], args.plugin_dir, args.max_turns, args.model)
        if err:
            return {"skill": skill_dir, "prompt": case["prompt"], "status": "ERROR",
                    "detail": err, "invoked": []}
        target = case["expect"] or case["expect_not"]
        fired = target in skills
        ok = fired if case["expect"] else not fired
        return {
            "skill": skill_dir, "prompt": case["prompt"],
            "status": "PASS" if ok else "FAIL",
            "mode": "expect" if case["expect"] else "expect_not",
            "target": target, "invoked": skills,
        }

    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for r in ex.map(run_one, work):
            results.append(r)
            mark = {"PASS": "  ok ", "FAIL": "FAIL ", "ERROR": "ERR  "}[r["status"]]
            extra = ""
            if r["status"] == "FAIL":
                extra = "  (invoked: %s)" % (", ".join(r["invoked"]) or "nothing")
            elif r["status"] == "ERROR":
                extra = "  (%s)" % r["detail"]
            print("%s %-14s %s%s" % (mark, r["skill"], r["prompt"][:64], extra), flush=True)

    npass = sum(1 for r in results if r["status"] == "PASS")
    nfail = sum(1 for r in results if r["status"] == "FAIL")
    nerr = sum(1 for r in results if r["status"] == "ERROR")
    rate = npass / len(results)
    print("\n%d passed, %d failed, %d errored — %.0f%% pass rate" % (npass, nfail, nerr, rate * 100))

    # Failures split by direction: a missed `expect` is weak routing, a tripped
    # `expect_not` is a skill firing when it should not. They mean different things.
    miss = [r for r in results if r["status"] == "FAIL" and r["mode"] == "expect"]
    over = [r for r in results if r["status"] == "FAIL" and r["mode"] == "expect_not"]
    if miss:
        print("  %d did not fire when expected (under-routing)" % len(miss))
    if over:
        print("  %d fired when they should not have (over-routing)" % len(over))

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(results, indent=2))
        print("wrote %s" % args.json)

    if nerr:
        sys.exit(2)
    sys.exit(0 if rate >= args.threshold else 1)


if __name__ == "__main__":
    main()
