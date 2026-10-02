# Findings derived from the MahoOS pilot

Evaluated upstream commit: `05542ba9132d21cc404930a9d0aa410bfba723de`

## CG-T004 — plain Python script execution is not an entry point

Severity: **Medium practical correctness / reachability**

MahoOS exposed this through `lib/maho_adaptive_shadow.py`, which ends with:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

The graph indexes calls made by `main()`, but `impact` and `reaches` report zero entry points.

A minimal reproduction is committed in:

`torture/fixtures/python/script-entry`

The fixture contains only:

```python
def target():
    ...

def main():
    target()

if __name__ == "__main__":
    raise SystemExit(main())
```

Observed:
- `main -> target` is indexed as an exact CALLS edge.
- `impact(target)` reports one transitive caller but `entry points: 0`.

Expected:
- direct script execution should be represented as a Python runtime entry path, or the entry-point feature should explicitly state that plain Python script entry is outside its model.

Why it matters:
- many CLI/service projects use thin shell wrappers that execute Python modules directly;
- reachability/impact grouping currently classifies code reachable from those script mains as “not reached from any indexed entry point”;
- this can make dead-code / runtime-impact interpretation misleading even when the Python call graph itself is correct.

Reproduction:

```bash
.venv/bin/python torture/harness/run.py --case T09-PY-SCRIPT-ENTRY
```

Machine-readable result: `realworld-derived-python-entry.json`.
