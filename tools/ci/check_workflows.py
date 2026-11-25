#!/usr/bin/env python3
"""Workflow lint for the fork-safety rules.

- Every workflow declares top-level `permissions`.
- Every action is pinned to a full commit SHA.
- A workflow that runs with a write token on pull request events
  (pull_request_target, issue_comment, workflow_run) never checks out
  or fetches pull request code. Code from a pull request runs only under
  `pull_request`, which gets a read-only token and no secrets.
"""

import pathlib
import re
import sys

import yaml

PRIVILEGED = {"pull_request_target", "issue_comment", "workflow_run"}
PR_CODE = re.compile(r"pull_request\.head|workflow_run\.head|refs/pull/|head_ref")
PINNED = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def triggers(wf: dict) -> set:
    on = wf.get("on", wf.get(True))  # YAML 1.1 reads a bare `on` key as True
    if isinstance(on, str):
        return {on}
    return set(on or [])


def check(path: pathlib.Path) -> list:
    wf = yaml.safe_load(path.read_text())
    errors = []
    if "permissions" not in wf:
        errors.append("no top-level permissions")
    privileged = triggers(wf) & PRIVILEGED
    for job_id, job in (wf.get("jobs") or {}).items():
        for step in job.get("steps") or []:
            uses = step.get("uses", "")
            if uses and not uses.startswith("./") and not PINNED.match(uses):
                errors.append(f"{job_id}: action not pinned to a commit SHA: {uses}")
            if privileged:
                text = str(step.get("with", {}).get("ref", "")) + str(step.get("run", ""))
                if PR_CODE.search(text):
                    errors.append(
                        f"{job_id}: checks out pull request code under {sorted(privileged)}"
                    )
    return [f"{path}: {e}" for e in errors]


def main() -> int:
    paths = sorted(pathlib.Path(".github/workflows").glob("*.y*ml"))
    errors = [e for p in paths for e in check(p)]
    print("\n".join(errors) or f"workflow lint: {len(paths)} workflows ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
