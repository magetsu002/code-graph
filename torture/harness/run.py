#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIXTURES = ROOT / "torture" / "fixtures"


def get_path(obj, dotted: str):
    cur = obj
    for part in dotted.split("."):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def check_op(actual, op: str, expected):
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "gt":
        return actual > expected
    if op == "gte":
        return actual >= expected
    if op == "lt":
        return actual < expected
    if op == "lte":
        return actual <= expected
    if op == "contains":
        return expected in actual
    raise ValueError(f"unknown op: {op}")


def index_case(case_dir: Path, truth: dict):
    td = tempfile.TemporaryDirectory(prefix="cg-torture-")
    db = Path(td.name) / "graph.db"
    env = dict(os.environ)
    env.update({str(k): str(v) for k, v in (truth.get("index_env") or {}).items()})
    env.setdefault("CODEGRAPH_NO_CACHE", "1")
    case_root = case_dir
    prep_logs = []
    if truth.get("prepare"):
        case_root = Path(td.name) / "fixture"
        shutil.copytree(case_dir, case_root)
        for command in truth["prepare"]:
            pp = subprocess.run(command, cwd=case_root, env=env, shell=True, capture_output=True, text=True)
            prep_logs.append({"command": command, "returncode": pp.returncode, "stdout": pp.stdout, "stderr": pp.stderr})
            if pp.returncode:
                raise RuntimeError(f"fixture prepare failed: {command}\n{pp.stderr}")
    cmd = [
        sys.executable, "-m", "codegraph.cli", "index", str(case_root),
        "--name", truth["id"], "--db", str(db),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    stats = json.loads(proc.stdout) if proc.returncode == 0 else None
    return td, db, proc, stats, prep_logs


def coverage_entry(stats: dict, language: str):
    return next((x for x in stats["coverage"]["languages"] if x["language"] == language), None)


def record(checks: list, name: str, ok: bool, actual=None, expected=None):
    checks.append({"name": name, "ok": bool(ok), "actual": actual, "expected": expected})


def run_case(truth_path: Path):
    truth = yaml.safe_load(truth_path.read_text())
    case_dir = truth_path.parent
    checks = []
    td, db, proc, stats, prep_logs = index_case(case_dir, truth)
    try:
        record(checks, "index exits 0", proc.returncode == 0, proc.returncode, 0)
        if proc.returncode != 0:
            return {
                "id": truth["id"], "title": truth["title"], "ok": False,
                "checks": checks, "stderr": proc.stderr[-4000:],
            }

        for lang, want in (truth.get("coverage") or {}).items():
            ent = coverage_entry(stats, lang)
            record(checks, f"coverage has {lang}", ent is not None, ent, "present")
            if ent is None:
                continue
            if isinstance(want, str):
                record(checks, f"{lang} coverage status", ent["status"] == want, ent["status"], want)
            else:
                if "status" in want:
                    record(checks, f"{lang} coverage status", ent["status"] == want["status"], ent["status"], want["status"])
                if "status_not" in want:
                    record(checks, f"{lang} coverage status is not {want['status_not']}",
                           ent["status"] != want["status_not"], ent["status"], f"not {want['status_not']}")
                if "files" in want:
                    record(checks, f"{lang} coverage file count", ent["files"] == want["files"], ent["files"], want["files"])

        for spec in truth.get("stats_checks") or []:
            actual = get_path(stats, spec["path"])
            op = spec.get("op", "eq")
            expected = spec["value"]
            record(checks, f"stats {spec['path']} {op} {expected}", check_op(actual, op, expected), actual, expected)

        con = sqlite3.connect(db)
        try:
            for nid in truth.get("nodes") or []:
                found = con.execute("SELECT 1 FROM nodes WHERE id=?", (nid,)).fetchone() is not None
                record(checks, f"node {nid}", found, found, True)
            for edge in truth.get("edges") or []:
                q = "SELECT confidence FROM edges WHERE src=? AND dst=? AND kind=?"
                rows = con.execute(q, (edge["src"], edge["dst"], edge["kind"])).fetchall()
                found = bool(rows)
                record(checks, f"edge {edge['src']} -{edge['kind']}-> {edge['dst']}", found, rows, "present")
                if found and edge.get("confidence"):
                    vals = {r[0] for r in rows}
                    record(checks, "edge confidence", edge["confidence"] in vals, sorted(vals), edge["confidence"])
            for edge in truth.get("absent_edges") or []:
                q = "SELECT confidence FROM edges WHERE src=? AND dst=? AND kind=?"
                rows = con.execute(q, (edge["src"], edge["dst"], edge["kind"])).fetchall()
                record(checks, f"edge absent {edge['src']} -{edge['kind']}-> {edge['dst']}",
                       not rows, rows, "absent")
        finally:
            con.close()


        for spec in truth.get("mcp") or []:
            from codegraph import mcp_server as M
            old = dict(M.STATE)
            try:
                M.STATE["db"] = str(db)
                fn = getattr(M, spec["tool"])
                text = fn(**(spec.get("args") or {}))
            finally:
                M.STATE.clear()
                M.STATE.update(old)
            for needle in spec.get("contains") or []:
                record(checks, f"MCP {spec['tool']} contains {needle!r}", needle in text, text, f"contains {needle!r}")
            any_needles = spec.get("contains_any") or []
            if any_needles:
                ok = any(n in text for n in any_needles)
                record(checks, f"MCP {spec['tool']} contains any completeness warning", ok, text, any_needles)
            for needle in spec.get("not_contains") or []:
                record(checks, f"MCP {spec['tool']} excludes {needle!r}", needle not in text, text, f"not contains {needle!r}")

        return {
            "id": truth["id"],
            "title": truth["title"],
            "ok": all(c["ok"] for c in checks),
            "checks": checks,
            "index_stderr": proc.stderr,
            "coverage": stats.get("coverage"),
            "prepare": prep_logs,
        }
    finally:
        td.cleanup()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", action="append", dest="cases")
    ap.add_argument("--report")
    args = ap.parse_args()

    truths = sorted(FIXTURES.rglob("truth.yaml"))
    if args.cases:
        wanted = set(args.cases)
        truths = [p for p in truths if yaml.safe_load(p.read_text()).get("id") in wanted]

    results = [run_case(p) for p in truths]
    out = {"cases": results, "passed": sum(r["ok"] for r in results), "failed": sum(not r["ok"] for r in results)}
    body = json.dumps(out, indent=2, default=str)
    print(body)
    if args.report:
        p = Path(args.report)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body + "\n")
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
