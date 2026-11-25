#!/usr/bin/env python3
"""Fail if any tracked file contains something that looks like a credential."""

import re
import subprocess
import sys

PATTERNS = {
    "AWS access key id": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
}


def main() -> int:
    files = subprocess.run(
        ["git", "ls-files", "-z"], check=True, capture_output=True, text=True
    ).stdout.split("\0")
    hits = 0
    for path in filter(None, files):
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        for lineno, line in enumerate(lines, 1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    print(f"{path}:{lineno}: possible {name}")
                    hits += 1
    print(f"secret scan: {hits} finding(s) in {len(files)} tracked files")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
