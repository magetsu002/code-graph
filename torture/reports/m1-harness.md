# M1 harness

The first ground-truth harness is in `torture/harness/run.py`.

It indexes each fixture into a temporary SQLite graph and can assert:
- per-language coverage state and file count
- arbitrary index-stat paths
- exact node presence
- exact edge presence and confidence
- MCP reply substrings

Positive control `CTRL-PY-001` verifies a direct Python call:
`function:app.caller -CALLS[exact]-> function:app.target`.

Result on upstream `05542ba9132d21cc404930a9d0aa410bfba723de`: PASS.

The harness exits non-zero when an expected trust property fails, so adversarial cases can be recorded as reproducible findings rather than informal observations.