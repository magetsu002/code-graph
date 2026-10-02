# M3 relationship matrix — first slice

Evaluated upstream commit: `05542ba9132d21cc404930a9d0aa410bfba723de`

The first precision/recall matrix targets ordinary Python and TypeScript relationships before moving into framework magic.

## Python — PASS

Fixture: `T05-PY-RELATIONSHIP-MATRIX`

Verified relationships:
- aliased direct function call: exact
- class instantiation: exact
- constructor call: exact
- typed receiver method call: resolved
- inherited receiver call: resolved
- class inheritance: exact
- override dispatch edge: resolved
- unique-method-name fallback: heuristic

Verified non-relationships:
- an untyped call with two same-named candidate methods did not invent either edge
- symbol-like text inside a string did not create call edges

All expected edge confidence labels matched.

## TypeScript — PASS

Fixture: `T06-TS-RELATIONSHIP-MATRIX`

Verified relationships:
- cross-file import: exact
- aliased function call: exact
- typed receiver method call: resolved
- class instantiation: exact

Verified non-relationships:
- symbol-like text inside a string did not create function/method call edges

## Current interpretation

The basic deterministic graph layer is behaving well on these fixtures. In particular, the tool did not inflate recall by inventing ambiguous Python dispatch edges, and it labelled the unique-name fallback as heuristic rather than resolved/exact.

No new defect is recorded from this slice. The next M3/M4 work should concentrate on wrappers, callbacks, decorators, DI, route construction and framework-specific magic, where static relationship recovery gets materially harder.

Machine-readable output: `m3-relationship-matrix.json`.