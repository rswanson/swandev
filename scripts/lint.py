#!/usr/bin/env python3
"""Deterministic structural lint for the swandev plugin repo.

Stdlib only. Runs six independent checks, always runs all of them (does not
stop at the first failure), and exits non-zero if any check fails.

Usage: python3 scripts/lint.py   (run from repo root)
"""

import glob
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Decision log #1: BUDGET = 2500 estimated tokens (current footprint is well
# under 2000, so the "current * 1.25" fallback does not apply here).
BUDGET = 2500

FRONTMATTER_RE = re.compile(
    r"^---\nname: (?P<name>[^\n]+)\ndescription: (?P<description>[^\n]+)\n---\n"
)

SWANDEV_REF_RE = re.compile(r"swandev:([a-z-]+)")


def rel(path):
    return os.path.relpath(path, REPO_ROOT)


def check_json_and_eval_shape():
    """(a) evals/*.eval.json and .claude-plugin/*.json parse as JSON; eval
    files are non-empty arrays of objects with exactly {query: str,
    should_trigger: bool}."""
    ok = True
    messages = []

    json_paths = sorted(
        glob.glob(os.path.join(REPO_ROOT, "evals", "*.eval.json"))
        + glob.glob(os.path.join(REPO_ROOT, ".claude-plugin", "*.json"))
    )

    if not json_paths:
        return False, ["no evals/*.eval.json or .claude-plugin/*.json files found"]

    for path in json_paths:
        p = rel(path)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            ok = False
            messages.append(f"{p}: invalid JSON: {exc}")
            continue

        is_eval_file = os.path.dirname(path) == os.path.join(REPO_ROOT, "evals")
        if not is_eval_file:
            # .claude-plugin/*.json: JSON parse is the only requirement.
            continue

        if not isinstance(data, list) or len(data) == 0:
            ok = False
            messages.append(f"{p}: must be a non-empty JSON array")
            continue

        for i, item in enumerate(data):
            if not isinstance(item, dict):
                ok = False
                messages.append(f"{p}[{i}]: expected an object, got {type(item).__name__}")
                continue
            keys = set(item.keys())
            if keys != {"query", "should_trigger"}:
                ok = False
                messages.append(
                    f"{p}[{i}]: expected exactly keys 'query', 'should_trigger', got {sorted(keys)}"
                )
                continue
            if not isinstance(item["query"], str):
                ok = False
                messages.append(f"{p}[{i}].query: expected str, got {type(item['query']).__name__}")
            if not isinstance(item["should_trigger"], bool):
                ok = False
                messages.append(
                    f"{p}[{i}].should_trigger: expected bool, got {type(item['should_trigger']).__name__}"
                )

    if ok:
        messages.append(f"parsed {len(json_paths)} JSON file(s), all eval files well-shaped")

    return ok, messages


def parse_skill_frontmatter(path):
    """Return (name, description) if the file starts with the exact expected
    frontmatter block, else None."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    return m.group("name"), m.group("description")


def check_skill_frontmatter():
    """(b) Every skills/*/SKILL.md starts with frontmatter
    ---\nname: <x>\ndescription: <one non-empty line>\n---\n where <x> equals
    its directory name."""
    ok = True
    messages = []

    skill_md_paths = sorted(glob.glob(os.path.join(REPO_ROOT, "skills", "*", "SKILL.md")))

    if not skill_md_paths:
        return False, ["no skills/*/SKILL.md files found"]

    for path in skill_md_paths:
        p = rel(path)
        dirname = os.path.basename(os.path.dirname(path))
        parsed = parse_skill_frontmatter(path)
        if parsed is None:
            ok = False
            messages.append(
                f"{p}: missing/malformed frontmatter "
                f"(expected '---\\nname: <x>\\ndescription: <line>\\n---\\n')"
            )
            continue
        name, description = parsed
        if name != dirname:
            ok = False
            messages.append(f"{p}: frontmatter name '{name}' does not match directory '{dirname}'")
        if not description.strip():
            ok = False
            messages.append(f"{p}: description is empty")

    if ok:
        messages.append(f"{len(skill_md_paths)} SKILL.md file(s) have valid frontmatter")

    return ok, messages


def check_bijection():
    """(c) skills/<name>/ <-> evals/<name>.eval.json, both directions."""
    ok = True
    messages = []

    skill_dirs = sorted(
        d for d in os.listdir(os.path.join(REPO_ROOT, "skills"))
        if os.path.isdir(os.path.join(REPO_ROOT, "skills", d))
    )
    eval_names = sorted(
        os.path.basename(p)[: -len(".eval.json")]
        for p in glob.glob(os.path.join(REPO_ROOT, "evals", "*.eval.json"))
    )

    skill_set = set(skill_dirs)
    eval_set = set(eval_names)

    missing_evals = sorted(skill_set - eval_set)
    missing_skills = sorted(eval_set - skill_set)

    for name in missing_evals:
        ok = False
        messages.append(f"skills/{name}/ has no matching evals/{name}.eval.json")
    for name in missing_skills:
        ok = False
        messages.append(f"evals/{name}.eval.json has no matching skills/{name}/")

    if ok:
        messages.append(f"{len(skill_set)} skill(s) each have exactly one matching eval file")

    return ok, messages


def check_dangling_refs():
    """(d) every swandev:<name> reference in skills/, evals/, README.md,
    .claude-plugin/*.json must name an existing skills/<name>/ directory."""
    ok = True
    messages = []

    skill_dirs = set(
        d for d in os.listdir(os.path.join(REPO_ROOT, "skills"))
        if os.path.isdir(os.path.join(REPO_ROOT, "skills", d))
    )

    scan_paths = []
    for pattern in ("skills/**/*", "evals/**/*"):
        scan_paths.extend(glob.glob(os.path.join(REPO_ROOT, pattern), recursive=True))
    scan_paths.append(os.path.join(REPO_ROOT, "README.md"))
    scan_paths.extend(glob.glob(os.path.join(REPO_ROOT, ".claude-plugin", "*.json")))

    scan_paths = sorted(set(p for p in scan_paths if os.path.isfile(p)))

    violations = 0
    total_refs = 0
    for path in scan_paths:
        p = rel(path)
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(lines, start=1):
            for m in SWANDEV_REF_RE.finditer(line):
                total_refs += 1
                ref_name = m.group(1)
                if ref_name not in skill_dirs:
                    ok = False
                    violations += 1
                    messages.append(f"{p}:{lineno}: dangling reference 'swandev:{ref_name}'")

    if ok:
        messages.append(f"{total_refs} swandev:<name> reference(s) all resolve to existing skills")

    return ok, messages


def check_manifest_sync():
    """(e) plugin.json and marketplace.json plugins[0] agree on version and
    description; plugin name matches."""
    ok = True
    messages = []

    plugin_path = os.path.join(REPO_ROOT, ".claude-plugin", "plugin.json")
    marketplace_path = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")

    try:
        with open(plugin_path, encoding="utf-8") as f:
            plugin = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return False, [f"{rel(plugin_path)}: cannot read/parse: {exc}"]

    try:
        with open(marketplace_path, encoding="utf-8") as f:
            marketplace = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return False, [f"{rel(marketplace_path)}: cannot read/parse: {exc}"]

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        return False, [f"{rel(marketplace_path)}: 'plugins' must be a non-empty array"]

    entry = plugins[0]

    for field in ("name", "version", "description"):
        if field not in plugin:
            ok = False
            messages.append(f"{rel(plugin_path)}: missing '{field}'")
        if field not in entry:
            ok = False
            messages.append(f"{rel(marketplace_path)}: plugins[0] missing '{field}'")

    if ok:
        if plugin["name"] != entry["name"]:
            ok = False
            messages.append(
                f"plugin name mismatch: plugin.json='{plugin['name']}' "
                f"marketplace.json plugins[0]='{entry['name']}'"
            )
        if plugin["version"] != entry["version"]:
            ok = False
            messages.append(
                f"version mismatch: plugin.json='{plugin['version']}' "
                f"marketplace.json plugins[0]='{entry['version']}'"
            )
        if plugin["description"] != entry["description"]:
            ok = False
            messages.append("description mismatch between plugin.json and marketplace.json plugins[0]")

    if ok:
        messages.append(
            f"plugin.json and marketplace.json agree: name='{plugin['name']}' version='{plugin['version']}'"
        )

    return ok, messages


def check_context_footprint():
    """(f) sum(len(description)) over all skill frontmatters / 4, must be
    within BUDGET."""
    skill_md_paths = sorted(glob.glob(os.path.join(REPO_ROOT, "skills", "*", "SKILL.md")))

    total_chars = 0
    unparsed = []
    for path in skill_md_paths:
        parsed = parse_skill_frontmatter(path)
        if parsed is None:
            unparsed.append(rel(path))
            continue
        _, description = parsed
        total_chars += len(description)

    tokens = total_chars // 4
    messages = [f"context footprint: ~{tokens} estimated tokens (budget {BUDGET})"]
    if unparsed:
        messages.append(
            f"note: {len(unparsed)} file(s) skipped (malformed frontmatter, see check b): "
            + ", ".join(unparsed)
        )

    ok = tokens <= BUDGET
    if not ok:
        messages.append(f"over budget: ~{tokens} tokens > {BUDGET} token budget")

    return ok, messages


CHECKS = [
    ("(a) JSON validity + eval shape", check_json_and_eval_shape),
    ("(b) SKILL.md frontmatter", check_skill_frontmatter),
    ("(c) skill/eval bijection", check_bijection),
    ("(d) dangling swandev: refs", check_dangling_refs),
    ("(e) manifest sync", check_manifest_sync),
    ("(f) context footprint budget", check_context_footprint),
]


def main():
    overall_ok = True
    for title, check_fn in CHECKS:
        ok, messages = check_fn()
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {title}")
        for msg in messages:
            print(f"    {msg}")
        overall_ok = overall_ok and ok

    print()
    if overall_ok:
        print("lint: all checks passed")
    else:
        print("lint: FAILED")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
