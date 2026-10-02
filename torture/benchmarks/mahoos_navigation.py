#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path


def timed(cmd: list[str], cwd: Path, runs: int = 9):
    samples = []
    out = None
    err = None
    rc = None
    subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    for _ in range(runs):
        t0 = time.perf_counter()
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        samples.append((time.perf_counter() - t0) * 1000)
        out, err, rc = p.stdout, p.stderr, p.returncode
    return {
        "command": cmd,
        "returncode": rc,
        "median_ms": round(statistics.median(samples), 3),
        "min_ms": round(min(samples), 3),
        "max_ms": round(max(samples), 3),
        "stdout_lines": len((out or "").splitlines()),
        "stdout": out,
        "stderr": err,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--runs", type=int, default=9)
    ap.add_argument("--out")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    snapshot = Path(args.snapshot).resolve()
    db = str(Path(args.db).resolve())
    py = str(Path(sys.executable).resolve())

    tasks = [
        {
            "id": "RW1-impact-recovery",
            "question": "What production code depends on plan_runtime_recovery?",
            "cg": [py, "-m", "codegraph.cli", "impact", "plan_runtime_recovery", "--db", db],
            "raw": ["git", "grep", "-n", "-w", "plan_runtime_recovery", "--", "lib"],
        },
        {
            "id": "RW2-adaptive-network-path",
            "question": "Can maho_adaptive_shadow.main reach network_proposals?",
            "cg": [py, "-m", "codegraph.cli", "path", "maho_adaptive_shadow.main",
                   "maho_adaptive_network.network_proposals", "--db", db],
            "raw": ["git", "grep", "-n", "-E",
                    "def main|def evaluate_shadow|evaluate_shadow\\(|policy_proposals\\(|network_proposals,",
                    "--", "lib/maho_adaptive_shadow.py"],
        },
        {
            "id": "RW3-admission-impact",
            "question": "Where is evaluate_admission used in production Python?",
            "cg": [py, "-m", "codegraph.cli", "impact", "evaluate_admission", "--db", db],
            "raw": ["git", "grep", "-n", "-w", "evaluate_admission", "--", "lib"],
        },
        {
            "id": "RW4-env-reader",
            "question": "Who reads MAHO_GUARDIAN_RECOVERY_ROOT?",
            "cg": [py, "-m", "codegraph.cli", "node", "env:MAHO_GUARDIAN_RECOVERY_ROOT", "--db", db],
            "raw": ["git", "grep", "-n", "MAHO_GUARDIAN_RECOVERY_ROOT", "--", "lib"],
        },

        {
            "id": "RW5-tests-recovery",
            "question": "What tests cover plan_runtime_recovery?",
            "cg": [py, "-m", "codegraph.cli", "tests", "plan_runtime_recovery", "--db", db],
            "raw": ["git", "grep", "-n", "-w", "plan_runtime_recovery", "--", "tests"],
        },
        {
            "id": "RW6-cli-entry",
            "question": "What launches maho_adaptive_shadow.py as a user-facing command?",
            "cg": [py, "-m", "codegraph.cli", "impact", "maho_adaptive_shadow.main", "--db", db],
            "raw": ["git", "grep", "-n", "maho_adaptive_shadow.py", "--", "bin", "systemd"],
        },
    ]

    result = {
        "snapshot": str(snapshot),
        "snapshot_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=snapshot, text=True).strip(),
        "db": db,
        "runs": args.runs,
        "tasks": [],
    }
    for task in tasks:
        result["tasks"].append({
            "id": task["id"],
            "question": task["question"],
            "cg": timed(task["cg"], root, args.runs),
            "raw": timed(task["raw"], snapshot, args.runs),
        })

    body = json.dumps(result, indent=2)
    body = body.replace(str(snapshot), "<snapshot>").replace(db, "<mahoos-lib.db>")
    print(body)
    if args.out:
        Path(args.out).write_text(body + "\n")


if __name__ == "__main__":
    main()
