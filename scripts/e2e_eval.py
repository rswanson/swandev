#!/usr/bin/env python3
"""Tier 3 behavioral e2e eval for the swandev plugin repo.

Stdlib only. Runs every scenario in scripts/e2e/scenarios.json as
`claude -p <prompt> --plugin-dir <repo root> --model claude-haiku-4-5
--output-format stream-json --verbose --max-turns 6 --allowedTools
"Skill,Read,Glob,Grep,Bash(git *)"` in a fresh, git-inited temp dir,
MAX_WORKERS at a time, parses the emitted stream-json event log, and
asserts each scenario's pass condition: no forbidden tool_use AND the
final assistant text matches final_text_regex.

Amendment (2026-08-03, evidence-based, see spec section 3): headless `-p`
sessions load plugin skills and expose the Skill tool, but neither Haiku
nor Sonnet proactively invokes skills there, even under an explicit
system-prompt directive. So scenarios invoke their skill EXPLICITLY via
`/swandev:<skill> <request>` as the prompt, and assertions measure gate
behavior only (once a skill is active, do its hard gates hold?), not
auto-invocation. Skill tool_use names are still collected and printed per
scenario as informational context, not asserted on.

Prints PASS/FAIL per scenario with evidence on failure and exits non-zero
if any scenario fails.

Usage: python3 scripts/e2e_eval.py   (run from repo root)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_PATH = os.path.join(REPO_ROOT, "scripts", "e2e", "scenarios.json")

MODEL = "claude-haiku-4-5"
MAX_TURNS = 6
MAX_WORKERS = 3
TIMEOUT_SECONDS = 300
ALLOWED_TOOLS = "Skill,Read,Glob,Grep,Bash(git *)"


def load_scenarios():
    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_scenario_cli(prompt):
    """Run the claude CLI for one scenario in a fresh, git-inited temp dir.

    Returns (ok, stdout_text, crash_evidence). ok is False on git-init
    failure, CLI timeout, non-zero exit, or spawn error, in which case
    crash_evidence is a short human-readable description (never a
    python traceback) and stdout_text is "".
    """
    tmpdir = tempfile.mkdtemp(prefix="e2e_eval_")
    try:
        init = subprocess.run(
            ["git", "init", "-q"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        if init.returncode != 0:
            detail = (init.stderr or init.stdout or "").strip()
            return False, "", f"git init failed in scenario tempdir: {detail[:200]}"

        try:
            proc = subprocess.run(
                [
                    "claude",
                    "-p",
                    prompt,
                    "--plugin-dir",
                    REPO_ROOT,
                    "--model",
                    MODEL,
                    "--output-format",
                    "stream-json",
                    "--verbose",
                    "--max-turns",
                    str(MAX_TURNS),
                    "--allowedTools",
                    ALLOWED_TOOLS,
                ],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return False, "", f"claude CLI timed out after {TIMEOUT_SECONDS}s"
        except OSError as exc:
            return False, "", f"claude CLI failed to start: {exc}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return False, proc.stdout, f"claude CLI exited {proc.returncode}: {detail[:300]}"

    return True, proc.stdout, None


def parse_stream(stdout_text):
    """Return (tool_calls, final_text) from stream-json stdout.

    tool_calls is a list of {"name", "input"} dicts in emission order,
    collected from every assistant event's tool_use content blocks.
    final_text is the "result" event's result string, falling back to
    the last assistant text block if no result event was emitted.
    Unparseable lines are silently ignored.
    """
    tool_calls = []
    last_assistant_text = None
    result_text = None

    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        obj_type = obj.get("type")
        if obj_type == "assistant":
            content = obj.get("message", {}).get("content", []) or []
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    tool_calls.append({"name": block.get("name"), "input": block.get("input")})
                elif block.get("type") == "text":
                    last_assistant_text = block.get("text")
        elif obj_type == "result":
            result_text = obj.get("result")

    final_text = result_text if result_text is not None else last_assistant_text
    return tool_calls, final_text


def evaluate_scenario(scenario, tool_calls, final_text):
    """Return (passed, evidence, invoked_skills) for one scenario given its
    parsed transcript. evidence is a list of human-readable failure reasons
    (empty when passed). A scenario passes iff no forbidden tool_use occurs
    AND final_text_regex matches the final assistant text; invoked_skills is
    informational only, not part of the pass/fail decision."""
    evidence = []

    invoked_skills = [
        tc["input"].get("skill")
        for tc in tool_calls
        if tc.get("name") == "Skill" and isinstance(tc.get("input"), dict)
    ]

    forbid_tools = scenario.get("forbid_tools") or []
    offending = [tc for tc in tool_calls if tc.get("name") in forbid_tools]
    if offending:
        for tc in offending:
            evidence.append(
                f"forbidden tool invoked: {tc['name']} input={json.dumps(tc.get('input'))[:200]}"
            )

    regex = scenario.get("final_text_regex")
    pattern = re.compile(regex, re.IGNORECASE | re.DOTALL)
    text_ok = bool(final_text) and bool(pattern.search(final_text))
    if not text_ok:
        evidence.append(f"final text did not match /{regex}/i: {json.dumps(final_text)[:400]}")

    passed = not offending and text_ok
    if passed:
        evidence = []

    return passed, evidence, invoked_skills


def run_scenario(scenario):
    start = time.monotonic()
    ok, stdout_text, crash_evidence = run_scenario_cli(scenario["prompt"])
    if not ok:
        duration = time.monotonic() - start
        return {
            "id": scenario["id"],
            "passed": False,
            "evidence": [crash_evidence],
            "invoked_skills": [],
            "final_text": None,
            "duration_s": duration,
        }

    tool_calls, final_text = parse_stream(stdout_text)
    passed, evidence, invoked_skills = evaluate_scenario(scenario, tool_calls, final_text)
    duration = time.monotonic() - start

    return {
        "id": scenario["id"],
        "passed": passed,
        "evidence": evidence,
        "invoked_skills": [s for s in invoked_skills if s],
        "final_text": final_text,
        "duration_s": duration,
    }


def main():
    scenarios = load_scenarios()
    if not scenarios:
        print("e2e_eval: no scenarios found in scripts/e2e/scenarios.json", file=sys.stderr)
        return 1

    overall_start = time.monotonic()
    results = [None] * len(scenarios)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_scenario, s): i for i, s in enumerate(scenarios)}
        for future in futures:
            i = futures[future]
            results[i] = future.result()
    overall_duration = time.monotonic() - overall_start

    any_failed = False
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        if not result["passed"]:
            any_failed = True
        skills_str = ", ".join(result["invoked_skills"]) if result["invoked_skills"] else "(none)"
        print(f"[{status}] {result['id']} ({result['duration_s']:.1f}s) skills invoked: {skills_str}")
        if not result["passed"]:
            for line in result["evidence"]:
                print(f"    {line}")

    print()
    print(f"e2e: {len(scenarios)} scenario(s) in {overall_duration:.1f}s wall-clock")
    if any_failed:
        print("e2e: FAILED")
        return 1

    print("e2e: all scenarios passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
