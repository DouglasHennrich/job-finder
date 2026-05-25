#!/usr/bin/env bash
# list-hooks.sh — Output all enabled hooks for a given event from extensions.yml
#
# Usage: bash .specify/scripts/bash/list-hooks.sh <event>
# Example: bash .specify/scripts/bash/list-hooks.sh after_tasks
#
# Output (one line per enabled hook):
#   COMMAND=<speckit_command> OPTIONAL=<true|false> PROMPT=<prompt_text>
#
# Exit codes:
#   0  — one or more hooks found
#   1  — no hooks found for the event (or event does not exist)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EXTENSIONS_FILE="$ROOT_DIR/.specify/extensions.yml"

if [[ $# -lt 1 ]]; then
  echo "Usage: list-hooks.sh <event>" >&2
  echo "Example: list-hooks.sh after_tasks" >&2
  exit 1
fi

EVENT="$1"

if [[ ! -f "$EXTENSIONS_FILE" ]]; then
  echo "Error: extensions.yml not found at $EXTENSIONS_FILE" >&2
  exit 1
fi

python3 - "$EXTENSIONS_FILE" "$EVENT" <<'PYEOF'
import sys
import re

extensions_file = sys.argv[1]
target_event = sys.argv[2]

with open(extensions_file, "r") as f:
    lines = f.readlines()

# State machine parser — no external deps
# Events are at 2-space indent: "  after_tasks:"
# Hook list items start with "  - " (2-space + dash + space)
# Hook properties at 4+ spaces: "    command: foo"

EVENT_RE = re.compile(r"^(\s+)(\w+):\s*$")
ITEM_RE  = re.compile(r"^\s+-\s")
PROP_RE  = re.compile(r"^(\s+)(\w+):\s*(.*)")

# Find the indentation level of the target event key
event_indent = None
event_found  = False
in_hooks     = False
hooks_key    = "hooks"

# First pass: determine if we're inside the hooks: block
# (event keys could appear outside hooks too)
# Strategy: find `hooks:` then look for the event key at consistent indent

# Simpler: find the event key that directly precedes hook list items
# by scanning for lines matching "  <event>:"
target_line_re = re.compile(r"^(\s+)" + re.escape(target_event) + r":\s*$")

collecting = False
event_indent_len = 0
hooks = []
current_hook = None

for raw_line in lines:
    line = raw_line.rstrip("\n")
    stripped = line.strip()

    # Skip blank lines and comment lines
    if not stripped or stripped.startswith("#"):
        continue

    if not collecting:
        m = target_line_re.match(line)
        if m:
            collecting = True
            event_indent_len = len(m.group(1))
        continue

    # We are inside the target event block.
    # Detect end: a key at same or lesser indent that is NOT a list item
    indent = len(line) - len(line.lstrip())

    if indent <= event_indent_len and not stripped.startswith("-"):
        # New sibling key or parent key — we've left the event block
        break

    # List item start: "  - extension: ..." or "  -"
    if re.match(r"^\s+-\s", line):
        if current_hook is not None:
            hooks.append(current_hook)
        current_hook = {}
        # The line itself may carry a key: "  - extension: git"
        rest = re.sub(r"^\s+-\s*", "", line)
        pm = re.match(r"(\w+):\s*(.*)", rest)
        if pm:
            current_hook[pm.group(1)] = pm.group(2).strip()
        continue

    # Property line inside a hook
    if current_hook is not None:
        pm = re.match(r"\s+(\w+):\s*(.*)", line)
        if pm:
            key = pm.group(1)
            val = pm.group(2).strip()
            # Remove trailing inline comments
            val = re.sub(r"\s+#.*$", "", val)
            # Remove surrounding quotes
            val = val.strip("\"'")
            current_hook[key] = val

if current_hook is not None:
    hooks.append(current_hook)

found = 0
for hook in hooks:
    enabled = str(hook.get("enabled", "true")).lower()
    if enabled == "false":
        continue
    command = hook.get("command", "")
    optional = str(hook.get("optional", "true")).lower()
    prompt = hook.get("prompt", "")
    if command:
        print(f"COMMAND={command} OPTIONAL={optional} PROMPT={prompt}")
        found += 1

sys.exit(0 if found > 0 else 1)
PYEOF
