#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python3 - "$repo_root" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])

# This checks the current working tree only. Git history and refs are outside its scope.
# Build sensitive strings from fragments so the scanner does not match itself.
patterns = {
    "personal home path": re.compile("/" + "Users" + "/", re.IGNORECASE),
    "tool-associated temporary path": re.compile("/" + "tmp/claude-" + r"\d+", re.IGNORECASE),
    "cloud-storage path": re.compile("i" + "Cloud", re.IGNORECASE),
    "owner name": re.compile("Al" + "mir", re.IGNORECASE),
    "owner account": re.compile("al" + "mir" + "sara" + "jcic", re.IGNORECASE),
    "owner surname": re.compile("Sara" + "jcic", re.IGNORECASE),
    "local project home": re.compile("~/" + "Areas/Kogen/", re.IGNORECASE),
    "local scratchpad path": re.compile(r"scratchpad/" + "work-" + r"[A-Za-z0-9._-]+", re.IGNORECASE),
    "unreserved sample email": re.compile("ann@" + "x.io", re.IGNORECASE),
    "checkout label": re.compile("krs" + "-v13", re.IGNORECASE),
}

actors = ["Open" + "AI", "Chat" + "GPT", "Co" + "dex", "Cl" + "aude", "A" + "I"]
actor_pattern = "(?:" + "|".join(re.escape(actor) for actor in actors) + ")"
action_pattern = "(?:generated|authored|written|created|reviewed|assisted|contributed)"
by_with = r"(?:\s+(?:by|with|using)\s+)"
patterns["AI attribution"] = re.compile(
    r"\b" + action_pattern + by_with + actor_pattern + r"\b|"
    + r"\b" + actor_pattern + r"\s+" + action_pattern + r"\b|"
    + actor_pattern + r"\s*\(\s*agent\s*\)|"
    + actor_pattern + r"\s+agent\b|"
    + r"\bagent\s*:\s*" + actor_pattern + r"\b|"
    + r"\b" + "A" + r"I[- ](?:generated|authored|written|created|assisted)\b|"
    + "co" + r"[- ]" + "authored" + r"[- ]by\b",
    re.IGNORECASE,
)

ignored_dirs = {".git", "__pycache__", ".venv", "node_modules"}
checked = 0
failures = []
for path in root.rglob("*"):
    if any(part in ignored_dirs for part in path.parts) or not path.is_file():
        continue
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    checked += 1
    for label, pattern in patterns.items():
        for match in pattern.finditer(content):
            line = content.count("\n", 0, match.start()) + 1
            failures.append(f"{path.relative_to(root)}:{line}: {label}")

if failures:
    print("Public scan failed:", file=sys.stderr)
    print("\n".join(failures), file=sys.stderr)
    sys.exit(1)

print(f"Public scan passed ({checked} files checked).")
PY
