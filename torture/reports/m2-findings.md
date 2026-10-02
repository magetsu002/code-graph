# M2 false-confidence findings

Evaluated upstream commit: `05542ba9132d21cc404930a9d0aa410bfba723de`

The positive control passes. Three adversarial Python cases and one TypeScript cache case were then run against the unmodified code-graph source.

## CG-T001 — file-level Python omissions still report exhaustive exact coverage

Severity: **High trust/correctness**

Two independent fixtures reproduce the same root problem.

### T01: parse failure

Fixture: `torture/fixtures/python/parse-error`

Ground truth:
- 2 Python source files are discovered.
- 1 source file fails to parse.
- index stats correctly record `plugins.python.parse_errors = 1`.

Actual:
- coverage reports `python 2 exact`.
- index stderr says `every source file cg found is indexed`.
- an MCP lookup for the symbol in the failed file returns no match and repeats the exhaustive coverage message.

Expected:
- file-level parse failure must make completeness visibly partial/degraded, or otherwise attach a query-level warning that the missing file was not represented.

Reproduction:
```bash
.venv/bin/python torture/harness/run.py --case T01-PY-PARSE-COVERAGE
```

### T03: valid oversized file skipped

Fixture: `torture/fixtures/python/oversized-file`

Ground truth:
- 2 valid Python source files are discovered.
- the fixture generates one valid source file larger than the plugin's 1,500,000-byte limit.
- index stats correctly record `plugins.python.skipped = 1`.

Actual:
- coverage reports `python 2 exact`.
- stderr again says every discovered source file is indexed.
- the hidden symbol is absent from the graph.
- the MCP no-match response has no uncovered-file fallback warning.

This is the stronger reproduction because the omitted file is valid source code.

Relevant implementation:
- `codegraph/plugins/python/plugin.py:35` defines the 1,500,000-byte limit.
- `codegraph/plugins/python/plugin.py:280` skips oversized files.
- `codegraph/plugins/python/plugin.py:311` records parsed/skipped/parse-error counts.
- `codegraph/coverage.py:59-70` currently converts a successfully running Python plugin to `exact` without checking those per-file counts.

Suggested direction:
- separate **analysis mode** (`exact/resolved/heuristic`) from **coverage completeness**.
- record discovered / parsed / skipped / parse-error counts in the coverage entry.
- never print `every source file ... is indexed` when those counts show an omission.
- empty/unknown-symbol MCP replies should name the omitted-file condition and recommend normal search.

Reproduction:
```bash
.venv/bin/python torture/harness/run.py --case T03-PY-OVERSIZED-SKIP
```

## CG-T002 — TypeScript facts cache can return stale exact relationships

Severity: **High correctness**

Fixture: `torture/fixtures/typescript/cache-stale`

Procedure:
1. index a TypeScript project where `run() -> foo()`; first facts cache result is `miss`.
2. change the source to `run() -> bar()`.
3. keep the file byte length identical and restore its original `mtime_ns`.
4. re-index the same project root.

Actual:
- second facts cache result is `hit`.
- the second graph still contains `run -CALLS[exact]-> foo`.
- there is no `run -> bar` edge.
- coverage still reports TypeScript exact.

The cache fingerprint currently uses file path plus `stat_key()`; `stat_key()` is size + mtime. Content is not part of the project-file fingerprint.

Relevant implementation:
- `codegraph/plugins/ts/plugin.py:315` — `facts_fingerprint`
- `codegraph/plugins/ts/plugin.py:334` — project file contribution uses `stat_key(p)`
- `codegraph/core/fsutil.py:37` — `stat_key` returns size and mtime

Suggested direction:
- include a content digest for source/config inputs, or use another invalidation mechanism that cannot return stale semantic facts after a content change.
- a cache hit should never allow old edges to be emitted as `exact` for different source bytes.

Reproduction:
```bash
.venv/bin/python torture/harness/cache_stale.py
```

## T02 — dynamic-dispatch honesty survived

Fixture: `torture/fixtures/python/dynamic-dispatch`

This case intentionally creates two classes with the same method and calls `service.do_work()` through an untyped parameter.

The graph does not invent an edge to either candidate, which is correct. More importantly, `impact(app.Alpha.do_work)` does **not** claim the method is certainly unused. The MCP response says it `may be called dynamically` and suggests broader graph/search checks.

Result: **PASS**.

This is worth preserving. The failure mode we care about is not merely an unresolved edge; it is an unresolved edge presented as exhaustive knowledge. This particular query avoids that trap.

## M2 status

Confirmed findings:
1. **CG-T001:** file-level Python omissions can coexist with `exact` / `every source file ... indexed` messaging.
2. **CG-T002:** TypeScript facts cache can serve stale exact edges when content changes without size/mtime changing.

Survived adversarial case:
- Python ambiguous dynamic dispatch gives an explicit dynamic-call caveat instead of fabricating an edge.

Raw machine-readable results:
- `m2-python.json`
- `m2-ts-cache.json`
