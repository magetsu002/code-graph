#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "torture" / "fixtures" / "typescript" / "cache-stale"


def index(project: Path, db: Path, cache: Path):
    env = dict(os.environ)
    env.pop("CODEGRAPH_NO_CACHE", None)
    env["CODEGRAPH_CACHE"] = str(cache)
    p = subprocess.run(
        [sys.executable, "-m", "codegraph.cli", "index", str(project), "--name", "T04-TS-CACHE", "--db", str(db)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    if p.returncode:
        raise RuntimeError(p.stderr)
    return json.loads(p.stdout), p.stderr


def run_targets(db: Path):
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT src,dst,confidence,file,line FROM edges "
            "WHERE kind='CALLS' AND src LIKE '%#run' ORDER BY dst"
        ).fetchall()
        return [list(r) for r in rows]
    finally:
        con.close()


def main():
    with tempfile.TemporaryDirectory(prefix="cg-torture-cache-") as td:
        td = Path(td)
        project = td / "project"
        cache = td / "cache"
        shutil.copytree(FIXTURE, project)
        src = project / "src" / "index.ts"

        st = src.stat()
        before = src.read_text()
        assert "return foo();" in before
        first_stats, first_err = index(project, td / "first.db", cache)
        first_edges = run_targets(td / "first.db")


        after = before.replace("return foo();", "return bar();")
        assert len(after.encode()) == len(before.encode())
        src.write_text(after)
        os.utime(src, ns=(st.st_atime_ns, st.st_mtime_ns))

        second_stats, second_err = index(project, td / "second.db", cache)
        second_edges = run_targets(td / "second.db")

        first_cache = first_stats["plugins"]["typescript"].get("facts_cache")
        second_cache = second_stats["plugins"]["typescript"].get("facts_cache")
        updated = any("bar" in row[1] for row in second_edges) and not any("foo" in row[1] for row in second_edges)
        out = {
            "id": "T04-TS-STALE-CACHE",
            "title": "same-size source change with restored mtime must invalidate TypeScript facts",
            "first_cache": first_cache,
            "second_cache": second_cache,
            "first_edges": first_edges,
            "second_edges": second_edges,
            "updated_relationship": updated,
            "first_stderr": first_err,
            "second_stderr": second_err,
        }
        print(json.dumps(out, indent=2))
        return 0 if updated else 1


if __name__ == "__main__":
    raise SystemExit(main())
