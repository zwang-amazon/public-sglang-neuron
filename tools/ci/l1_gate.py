#!/usr/bin/env python3
"""Trainium CI (L1) policy: who runs L1, maintainer approval, and the aggregate gate status.

Every caller runs this file from a checkout of the default branch, so a pull request
cannot change the policy that judges it. The script reads pull request metadata
through the REST API and never checks out or runs code from a pull request.

Commands:
  authorize  used by the L1 workflow (pull_request): decide whether the stub
             Trainium tests run for one commit.
  handle     used by the gate workflow: clear approval on a new push from an
             unlisted author, and record approval from a maintainer
             (`run-ci` label or a `/tag-and-rerun-ci` comment).
  evaluate   used by the gate workflow: post the required `L1 Trainium gate`
             status on the pull request head.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ROOT = pathlib.Path(__file__).resolve().parents[2]

HARDWARE_PATHS = ("sglang_neuron/kernels/",)
PROTECTED_PATHS = (".github/",)
RUN_CI_LABEL = "run-ci"
COMMAND = "/tag-and-rerun-ci"
APPROVAL_CONTEXT = "ci/run-ci-approved"
GATE_CONTEXT = "L1 Trainium gate"
L1_WORKFLOW = "l1-trainium.yml"
L1_TEST_JOB = "Trainium tests (stub)"
APPROVER_ROLES = {"admin", "maintain"}
BOT = "github-actions[bot]"


def api(method: str, path: str, body: dict | None = None, ok404: bool = False):
    url = path if path.startswith("https://") else f"{API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as err:
        if ok404 and err.code == 404:
            return None
        detail = err.read().decode(errors="replace")[:300]
        raise SystemExit(f"{method} {url}: HTTP {err.code}: {detail}") from err


def paginate(path: str) -> list:
    sep = "&" if "?" in path else "?"
    out, page = [], 1
    while True:
        items = api("GET", f"{path}{sep}per_page=100&page={page}")
        out.extend(items)
        if len(items) < 100:
            return out
        page += 1


def ci_permissions() -> dict:
    with open(ROOT / ".github" / "CI_PERMISSIONS.json") as f:
        return json.load(f)


def is_listed(user: str) -> bool:
    return bool(ci_permissions().get(user, {}).get("can_tag_run_ci_label"))


def is_approver(user: str) -> bool:
    data = api("GET", f"/repos/{REPO}/collaborators/{user}/permission", ok404=True)
    return bool(data) and data.get("role_name") in APPROVER_ROLES


def changed_files(pr_number: int) -> list[str]:
    files = []
    for f in paginate(f"/repos/{REPO}/pulls/{pr_number}/files"):
        files.append(f["filename"])
        if f.get("previous_filename"):
            files.append(f["previous_filename"])
    return files


def touches(files: list[str], prefixes: tuple[str, ...]) -> bool:
    return any(f.startswith(prefixes) for f in files)


def head_approved(sha: str) -> bool:
    # Statuses come newest first; the latest one for the context decides.
    for s in paginate(f"/repos/{REPO}/commits/{sha}/statuses"):
        if s["context"] == APPROVAL_CONTEXT:
            return s["state"] == "success" and (s.get("creator") or {}).get("login") == BOT
    return False


def post_status(sha: str, context: str, state: str, description: str, url: str = "") -> None:
    body = {"state": state, "context": context, "description": description[:140]}
    if url:
        body["target_url"] = url
    api("POST", f"/repos/{REPO}/statuses/{sha}", body)
    print(f"status {context!r} on {sha[:12]}: {state}: {description}")


def comment(number: int, text: str) -> None:
    api("POST", f"/repos/{REPO}/issues/{number}/comments", {"body": text})


def remove_label(number: int) -> None:
    api("DELETE", f"/repos/{REPO}/issues/{number}/labels/{RUN_CI_LABEL}", ok404=True)


def labels(pr: dict) -> set[str]:
    return {label["name"] for label in pr.get("labels", [])}


def latest_l1_run(sha: str) -> dict | None:
    runs = api(
        "GET",
        f"/repos/{REPO}/actions/workflows/{L1_WORKFLOW}/runs?head_sha={sha}&event=pull_request",
    )["workflow_runs"]
    runs.sort(key=lambda r: r["created_at"], reverse=True)
    return runs[0] if runs else None


def l1_test_job(run: dict) -> dict | None:
    for job in api("GET", f"{run['jobs_url']}?per_page=100")["jobs"]:
        if job["name"] == L1_TEST_JOB:
            return job
    return None


# --- authorize -------------------------------------------------------------


def cmd_authorize(args) -> int:
    pr = api("GET", f"/repos/{REPO}/pulls/{args.pr}")
    author = pr["user"]["login"]
    files = changed_files(args.pr)
    if not touches(files, HARDWARE_PATHS):
        run, why = False, "no hardware paths changed; L1 is not required"
    elif is_listed(author):
        run, why = True, f"author @{author} is listed in .github/CI_PERMISSIONS.json"
    elif head_approved(args.sha):
        run, why = True, f"a maintainer approved commit {args.sha[:12]}"
    else:
        run, why = False, f"waiting for a maintainer to approve {args.sha[:12]} ({COMMAND})"
    print(f"::notice::Trainium tests {'run' if run else 'skipped'}: {why}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"run={'true' if run else 'false'}\n")
    return 0


# --- handle ----------------------------------------------------------------


def approve(pr: dict, approver: str) -> None:
    """Approve the current head commit and re-run its L1 run, which then reads the approval."""
    sha = pr["head"]["sha"]
    post_status(sha, APPROVAL_CONTEXT, "success", f"Trainium CI approved by @{approver}")
    for _ in range(36):
        run = latest_l1_run(sha)
        if run is None:
            print("no L1 run for this commit yet; it will read the approval when it starts")
            return
        if run["status"] == "completed":
            api("POST", f"/repos/{REPO}/actions/runs/{run['id']}/rerun")
            print(f"re-ran L1 run {run['html_url']}")
            return
        time.sleep(5)
    print(f"L1 run {run['html_url']} did not finish in time; re-run it by hand")


def cmd_handle(args) -> int:
    event = json.loads(pathlib.Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    name = os.environ["GITHUB_EVENT_NAME"]

    if name == "pull_request_target":
        pr = event["pull_request"]
        author = pr["user"]["login"]
        action = event["action"]
        if action == "synchronize" and not is_listed(author) and RUN_CI_LABEL in labels(pr):
            remove_label(pr["number"])
            comment(
                pr["number"],
                f"New commits were pushed, so Trainium CI approval is cleared. A maintainer "
                f"reviews the new commits and comments `{COMMAND}` to approve again.",
            )
        elif action == "unlabeled" and event["label"]["name"] == RUN_CI_LABEL:
            sender = event["sender"]["login"]
            if sender != BOT and is_approver(sender) and not is_listed(author):
                post_status(
                    pr["head"]["sha"], APPROVAL_CONTEXT, "failure", f"Withdrawn by @{sender}"
                )
        elif action == "labeled" and event["label"]["name"] == RUN_CI_LABEL:
            sender = event["sender"]["login"]
            if sender == BOT:
                return 0
            if is_approver(sender):
                approve(pr, sender)
            else:
                remove_label(pr["number"])
                comment(pr["number"], f"Only maintainers can add `{RUN_CI_LABEL}`.")
        return 0

    if name == "issue_comment":
        lines = [ln.strip() for ln in event["comment"]["body"].splitlines()]
        if "pull_request" not in event["issue"] or COMMAND not in lines:
            return 0
        number = event["issue"]["number"]
        user = event["comment"]["user"]["login"]
        if not is_approver(user):
            comment(number, f"@{user} only maintainers can run `{COMMAND}`.")
            return 0
        pr = api("GET", f"/repos/{REPO}/pulls/{number}")
        api("POST", f"/repos/{REPO}/issues/{number}/labels", {"labels": [RUN_CI_LABEL]})
        approve(pr, user)
        return 0

    return 0


# --- evaluate --------------------------------------------------------------


def gate_for(pr: dict) -> tuple[str, str, str]:
    sha = pr["head"]["sha"]
    author = pr["user"]["login"]
    files = changed_files(pr["number"])
    trusted = is_listed(author) or head_approved(sha)
    if touches(files, PROTECTED_PATHS) and not trusted:
        return "failure", f"Changes .github/; needs maintainer approval ({COMMAND})", ""
    if not touches(files, HARDWARE_PATHS):
        return "success", "No hardware paths changed; L1 not required", ""
    run = latest_l1_run(sha)
    if run is None:
        return "pending", "Waiting for L1 Trainium CI to start", ""
    url = run["html_url"]
    if run["status"] != "completed":
        return "pending", "L1 Trainium CI is running", url
    job = l1_test_job(run)
    conclusion = job["conclusion"] if job else None
    if conclusion == "success":
        return "success", "Trainium tests passed on this commit", url
    if conclusion == "skipped" or job is None:
        if trusted:
            return "pending", "Trainium tests did not run; re-run L1", url
        return "pending", f"Hardware paths changed; waiting for maintainer {COMMAND}", url
    return "failure", f"Trainium tests {conclusion}", url


def cmd_evaluate(args) -> int:
    if args.pr:
        prs = [api("GET", f"/repos/{REPO}/pulls/{args.pr}")]
    else:
        prs = paginate(f"/repos/{REPO}/pulls?state=open")
        prs = [p for p in prs if p["head"]["sha"] == args.sha]
    if not prs:
        print("no open pull request for this commit")
    for pr in prs:
        if pr["state"] != "open":
            continue
        state, description, url = gate_for(pr)
        post_status(pr["head"]["sha"], GATE_CONTEXT, state, description, url)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("authorize")
    a.add_argument("--pr", type=int, required=True)
    a.add_argument("--sha", required=True)
    sub.add_parser("handle")
    e = sub.add_parser("evaluate")
    e.add_argument("--pr", type=int)
    e.add_argument("--sha")
    args = parser.parse_args()
    if not REPO or not TOKEN:
        raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN must be set")
    return {"authorize": cmd_authorize, "handle": cmd_handle, "evaluate": cmd_evaluate}[args.cmd](
        args
    )


if __name__ == "__main__":
    sys.exit(main())
