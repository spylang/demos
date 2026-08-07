#!/usr/bin/env python3
"""
Format SPy redshifted code using ruff format.

Reads redshifted SPy code from stdin, temporarily replaces invalid Python
tokens with length-preserving Unicode substitutes, runs `ruff format`, then
restores the original names (with ANSI coloring) and prints to stdout.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Character substitution tables (all 1-char → 1-char, preserving length)
# All substitutes are valid Python identifier characters (ID_Continue).
# ---------------------------------------------------------------------------

FORWARD = str.maketrans(
    {
        "[": "ᐸ",  # U+1438  CANADIAN SYLLABICS PA         (looks like <)
        "]": "ᐳ",  # U+1433  CANADIAN SYLLABICS PO         (looks like >)
        ",": "ᐤ",  # U+1424  CANADIAN SYLLABICS FINAL RING (comma inside names)
        "#": "፩",  # U+1369  ETHIOPIC DIGIT ONE
        " ": "·",  # U+00B7  MIDDLE DOT
    }
)
BACKWARD = str.maketrans({v: k for k, v in FORWARD.items()})

# 2-char substitutions (same length, handled with str.replace)
DOUBLE_FORWARD = [("::", "ːː")]  # U+02D0  MODIFIER LETTER TRIANGULAR COLON  ×2
DOUBLE_BACKWARD = [(new, old) for old, new in DOUBLE_FORWARD]

# Characters that signal a token was modified (used to detect what to unfix)
SPECIAL_CHARS = "".join(
    [
        "ᐸ",  # U+1438  [ substitute
        "ᐳ",  # U+1433  ] substitute
        "ᐤ",  # U+1424  , substitute
        "፩",  # U+1369  # substitute
        "·",  # U+00B7  space substitute
        "ː",  # U+02D0  : substitute (used doubled for ::)
    ]
)

# Matches any identifier-like token that may contain our special chars
TOKEN_RE = re.compile(rf"[\w{re.escape(SPECIAL_CHARS)}]+")

# Matches a backtick-quoted name in the redshifted source
BACKTICK_RE = re.compile(r"`([^`]+)`")

# Matches a bare $-prefixed name (e.g. $v0, _$iter0) — not backtick-quoted
DOLLAR_RE = re.compile(r"\$")
DOLLAR_SUB = "ꞩ"  # U+A7A9  LATIN SMALL LETTER S WITH OBLIQUE STROKE

# Matches ANSI escape sequences (e.g. \x1b[34;01m or \x1b[00m)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# ANSI color for backtick-quoted names — bright magenta, matching spy redshift
ANSI_NAME = "\x1b[35;01m"
ANSI_RESET = "\x1b[00m"


# ---------------------------------------------------------------------------
# Name-level transformations
# ---------------------------------------------------------------------------


def fix_name(name: str) -> str:
    """Replace invalid Python identifier chars inside a backtick-quoted name."""
    for old, new in DOUBLE_FORWARD:
        name = name.replace(old, new)
    return name.translate(FORWARD)


def unfix_name(name: str) -> str:
    """Reverse fix_name."""
    name = name.translate(BACKWARD)
    for old, new in DOUBLE_BACKWARD:
        name = name.replace(old, new)
    return name


# ---------------------------------------------------------------------------
# Code-level transformations
# ---------------------------------------------------------------------------


def fix_code(code: str) -> str:
    """Replace every `backtick-quoted name` and bare $-name with valid Python identifiers."""
    code = ANSI_RE.sub("", code)
    code = BACKTICK_RE.sub(lambda m: fix_name(m.group(1)), code)
    code = DOLLAR_RE.sub(DOLLAR_SUB, code)
    return code


def unfix_code(code: str, color: bool = True) -> str:
    """Restore every modified identifier to its original form."""

    def maybe_unfix(m: re.Match) -> str:
        token = m.group()
        if any(c in token for c in SPECIAL_CHARS):
            name = f"`{unfix_name(token)}`"
            return f"{ANSI_NAME}{name}{ANSI_RESET}" if color else name
        if DOLLAR_SUB in token:
            return token.replace(DOLLAR_SUB, "$")
        return token

    return TOKEN_RE.sub(maybe_unfix, code)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    color = sys.stdout.isatty()
    original = sys.stdin.read()
    fixed = fix_code(original)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(fixed)
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            ["ruff", "format", "--line-length", "89", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print("ruff format failed:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)

        formatted = tmp_path.read_text(encoding="utf-8")
    finally:
        tmp_path.unlink()

    print(unfix_code(formatted, color=color), end="")


if __name__ == "__main__":
    main()
