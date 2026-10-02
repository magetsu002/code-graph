# code-graph adversarial evaluation

This directory contains a reproducible torture suite for code-graph. The goal is not to produce random crashes; it is to measure where the graph is correct, where it is incomplete, and whether incomplete results are communicated honestly to an AI agent.

## Rules

- Do not modify codegraph/ to make a failing torture case pass until the failure is recorded.
- Every finding is tied to an upstream commit SHA and a minimal fixture.
- Separate missing relationships from silent missing relationships.
- Verify every claimed false positive or false negative against fixture ground truth.
- Security testing comes after developer-correctness testing and uses disposable canary data only.

## Milestones

- M0: clean baseline and upstream test suite
- M1: ground-truth harness
- M2: coverage / false-confidence torture
- M3: relationship precision and recall
- M4: framework-specific edge cases
- M5: mutation testing
- M6: real-repository scale tests
- M7: repeated AI A/B benchmark
- M8: sandboxed security testing
- M9: review and feedback report

Reports live in torture/reports/.