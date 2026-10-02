# MahoOS real-world navigation benchmark

Snapshot: `dcea6e3c584c9d7ae95c46e3b0f07c97c921c48e`

Code-graph DB: MahoOS `lib/` indexed as its own Python project root (137/137 files parsed, 2,247 nodes, 7,342 edges).

This benchmark asks practical repository-navigation questions rather than synthetic graph questions. Each task compares a code-graph query with a simple `git grep` retrieval baseline. Timings are 11 warm runs and measure retrieval process latency only; they do not measure the human/agent reasoning needed after the output.

## Results

| Task | CG median | grep median | Result |
|---|---:|---:|---|
| RW1 impact of `plan_runtime_recovery` | 48.8 ms | 3.5 ms | **CG strongly useful** |
| RW2 path `main -> network_proposals` | 49.6 ms | 4.1 ms | **CG misses real path** |
| RW3 impact of `evaluate_admission` | 52.9 ms | 3.8 ms | **CG strongly useful** |
| RW4 env reader | 49.4 ms | 4.9 ms | **Both useful; grep simpler** |
| RW5 tests covering recovery planner | 53.1 ms | 4.5 ms | **CG not useful here** |
| RW6 user-facing CLI entry | 49.8 ms | 6.2 ms | **CG misses cross-language entry** |

The absolute CG latency is still sub-100ms, so process latency is not the important tradeoff. The value is whether the structured answer removes follow-up searches.

## RW1 — impact of plan_runtime_recovery

Question: **What production code depends on `plan_runtime_recovery`?**

Raw search returns the definition plus six direct call sites.

Code-graph returns those six direct callers plus two transitive callers in one query:
- `guardian_live_recovery.recovery_loop`
- `guardian_runtime_recovery_campaign.main`

The `reaches` query also provides exact evidence chains with file/line locations.

This is a real productivity win. A text search is faster as a process but does not answer the transitive-impact question without more searches and code reading.

Result: **CG strongly useful.**

## RW2 — real adaptive-policy path

Question: **Can `maho_adaptive_shadow.main` reach `network_proposals`?**

Code-graph says:

```text
no forward path from maho_adaptive_shadow.main to maho_adaptive_network.network_proposals
```

The source contains a real runtime path:

```text
main
 -> evaluate_shadow
 -> policy_proposals
 -> tuple containing network_proposals
 -> policy(snapshot, ...)
```

The callback/function-value flow is not represented, so the graph cannot prove a path that actually exists.

The separate `impact network_proposals` response is more honest: it says there are no recorded callers but the function may be called dynamically. That caveat is good, but `path` still returns a clean negative result.

Result: **CG misses a real production path; fallback search is required.**

## RW3 — admission impact

Question: **Where can `evaluate_admission` affect production code?**

Raw search shows one direct production call in `guardian_native_admission.admit_candidate`.

Code-graph returns 11 transitive dependents across admission and update flows, including:
- `candidate_first_admission`
- `guardian_native_admission.main`
- both production-candidate evaluators
- native update campaign execution/approval
- normal-host guardian admission
- normal update certification

The evidence paths show exact edges except where receiver resolution is explicitly marked `resolved`.

Spot checks against the source confirm the paths.

This is the clearest real-world value proposition so far: **one structured query replaces a manual chain of repeated symbol searches.**

Result: **CG strongly useful.**

## RW4 — environment variable reader

Question: **Who reads `MAHO_GUARDIAN_RECOVERY_ROOT`?**

Code-graph directly reports:

```text
READS_ENV method:guardian_live_state.LivePaths.defaults
@guardian_live_state.py:92 exact
```

Raw grep returns the same single source line.

The graph result is semantically nicer, but for a unique literal this is not a meaningful advantage over ordinary search.

Result: **correct and useful, but grep is sufficient.**

## RW5 — tests covering plan_runtime_recovery

Question: **What tests exercise `plan_runtime_recovery`?**

Code-graph reports:

```text
tests: 0 direct, 0 transitive (of 0 test cases in the graph)
```

Raw repository search finds four direct call sites across three Python test files:
- `tests/test_guardian_live_recovery.py`
- `tests/test_guardian_runtime_auto_response.py`
- `tests/test_guardian_runtime_integrity_incident.py` (two call sites)

This is not a false statement about the current DB—the query says the graph has no test nodes—but it makes the advertised `tests` feature ineffective for a Python-heavy project such as MahoOS.

Current test indexing is oriented around PHP/JS test conventions rather than Python/pytest.

Result: **not useful for MahoOS test coverage today.**

## RW6 — user-facing CLI entry

Question: **What launches `maho_adaptive_shadow.py`?**

Code-graph reports no recorded caller for `maho_adaptive_shadow.main` and zero indexed entry points.

Raw whole-repository search immediately finds:

```bash
bin/maho-adaptive:
exec python "$ROOT/lib/maho_adaptive_shadow.py" "$@"
```

This is a normal cross-language boundary in MahoOS. Shell is not part of the graph, so application entry reachability stops before the actual user-facing command.

Result: **CG alone is incomplete for whole-system entry analysis.**

## Practical workflow conclusion

The best MahoOS workflow is not **CG instead of repository search**.

It is:

1. use CG first for supported-language impact/reachability questions;
2. trust its positive exact/resolved evidence paths after normal spot verification;
3. treat negative answers (`no path`, `no callers`, `0 tests`) as prompts to inspect coverage/capabilities and fall back to raw search;
4. use raw search immediately at language/process boundaries (shell, QML, generated/runtime registration).

On the questions CG handles well, it compresses several manual searches into one structured answer. On the questions it does not model, ordinary repository search remains essential.

## Product feedback from the real project

1. **Custom Python source roots are important.** MahoOS only becomes useful when `lib/` is indexed as the Python root. A configuration such as `python_source_roots = ["lib"]` or an equivalent CLI option would avoid requiring users to choose a narrower project manually.

2. **Coverage should inventory source extensions it does not understand.** MahoOS has 113 QML files and 95 shell files. They are absent from the coverage report rather than explicitly counted as unsupported/ignored source.

3. **File coverage and semantic completeness need separate concepts.** A language can be fully parsed while callbacks, framework magic or generated behavior remain outside the graph.

4. **Function-value/callback flow deserves at least a reference edge.** MahoOS's policy tuple is a natural example. Even a `REFERENCES_FN` edge from `policy_proposals` to `network_proposals` would make impact analysis less misleading.

5. **Cross-language entry detection would be valuable.** Simple shell patterns such as `exec python path/to/file.py` could create a low-risk entry/reference edge, or at minimum coverage should tell the agent that shell launchers are outside the graph.

6. **Python/pytest test discovery would materially improve the `tests` feature.** MahoOS has a large Python test suite that currently produces zero graph test nodes.

7. **Negative query wording should stay conservative.** Prefer `no recorded path` over `no forward path` when known semantic/cross-language gaps exist, and attach relevant capability warnings.

8. **Project-root ergonomics matter as much as parser quality.** Whole-repo MahoOS indexing initially saw 288 Python files but indexed none; the right subproject root changed the tool from nearly useless to genuinely helpful.

## Positive feedback worth preserving

- impact/reaches evidence chains are genuinely useful on real code;
- exact/resolved/heuristic labels make the output much easier to trust than an unlabelled relationship graph;
- direct and typed Python calls performed well in the earlier adversarial matrix;
- ambiguous dynamic dispatch did not invent edges;
- the no-caller response already warns about dynamic invocation;
- once configured correctly, indexing ~137 Python files takes only a couple seconds and query latency is operationally negligible.

Machine-readable benchmark output: `realworld-mahoos-navigation.json`.
