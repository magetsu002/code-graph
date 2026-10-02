# Real-world pilot: MahoOS

This is an evaluation of code-graph against a frozen, disposable MahoOS snapshot. No files were changed in the MahoOS repository and no evaluation artifacts are stored there.

MahoOS snapshot commit: `dcea6e3c584c9d7ae95c46e3b0f07c97c921c48e`
Source branch at snapshot time: `fix/m4b-initramfs-recovery`

The active MahoOS working tree was intentionally left untouched because it had a local modification.

## Repository shape

Tracked source corpus is roughly:
- 288 Python files, ~65.7k lines
- 113 QML files, ~28.7k lines
- 95 shell files, ~15.5k lines
- 12 C/C++ headers/sources, ~3.2k lines
- 9 Lua files
- 2 JavaScript files

This makes MahoOS a useful real-world test because it is multi-language, non-framework-shaped, and contains custom project structure instead of a conventional Python package root.

## Out-of-box indexing

Indexing the repository root without modifying the snapshot completed quickly (~0.33 s wall, ~40 MB child max RSS) but was not practically useful for most of the project.

Observed coverage:
- Python: 288 files, **not indexed**
- JavaScript/TypeScript bucket: 2 files, not indexed
- C/C++: 12 files, heuristic
- Lua: 9 files, unsupported
- QML: 113 files are not represented in the coverage report at all

Graph size: 335 nodes / 725 edges.

The root reason for Python is project detection: MahoOS has no root `pyproject.toml`, `requirements.txt`, `setup.py`, `manage.py`, etc. The Python source is organized under project directories instead.

This is useful feedback: on a large real repository, code-graph's first-run usefulness depends heavily on project-root conventions. Its coverage warning is good for Python, but QML is a major part of MahoOS and is invisible rather than explicitly listed unsupported.

## Root-assisted run

A temporary `pyproject.toml` marker was added only to a disposable copy to give code-graph the best chance to index Python from the repository root.

Performance:
- ~3.63 s wall
- ~163 MB child max RSS
- 3,080 nodes / 9,696 edges

Python plugin stats:
- files discovered: 288
- parsed modules: 264
- skipped: 0
- parse errors: 0
- reported coverage: **python 288 exact**

The mismatch matters: 24 real Python files never became modules, but coverage still says exact and prints `every source file cg found is indexed`.

Examples of omitted real MahoOS files include:
- `apps/maho-files/source-fingerprint.py`
- `config/quickshell/maho-link/bluetooth.py`
- `config/quickshell/maho-link/wifi.py`
- `config/quickshell/maho-lock/state.py`
- `config/quickshell/maho-shell/state.py`
- several tests and operational tools

These paths contain hyphenated directory/file components that do not map cleanly to Python module identifiers. This reproduces CG-T001 on a real project rather than a synthetic fixture.

There is a second practical issue: indexing Python from the MahoOS repository root produced `imports: 0`. MahoOS's `lib/` code is commonly imported as top-level modules at runtime, so canonicalizing it as `lib.<module>` prevents many cross-module links from resolving.

## Subproject indexing is materially more useful

Indexing MahoOS's `lib/` directory as its own project root is a much better fit.

Performance:
- ~2.21 s wall
- ~125 MB child max RSS
- 137/137 Python files parsed
- 723 imports resolved
- 2,247 nodes / 7,342 edges
- 4,485 exact calls, 388 resolved calls, 6 heuristic calls

A concrete impact query on `plan_runtime_recovery` was useful.

Code-graph found all six direct production callers visible by raw source inspection:
- four callers in `guardian_live_recovery.py`
- two callers in `guardian_runtime_recovery_campaign.py`

It also found two transitive callers and returned evidence paths with file/line locations in one query. That is genuinely better than a plain text search for understanding impact.

For `evaluate_admission`, code-graph correctly found the production caller in `guardian_native_admission.py`.

This is the first strong real-world positive result: **when the project root matches the import model, impact navigation is fast and useful.**

## Real-world miss: callback flow

`maho_adaptive_shadow.policy_proposals()` builds a tuple of policy functions including `network_proposals` and later invokes each through a local variable:

```python
for policy in (
    battery_proposals,
    thermal_proposals,
    workload_proposals,
    network_proposals,
    ...
):
    proposals.extend(policy(snapshot, created_at=now))
```

Raw source inspection shows this is a real runtime use of `network_proposals`.

The graph records zero incoming call/reference edges to `network_proposals`. An impact query therefore says there are no recorded callers, although it appropriately adds that the function may be called dynamically and recommends broader search.

This is a reasonable static-analysis limitation, but it is important product feedback: callback/function-value flow is common in real code and can make impact results incomplete even when language coverage is reported exact.

## Initial product feedback from MahoOS

What helped:
- very fast indexing once the correct subproject root was chosen
- impact queries collapse multiple call levels into one answer
- evidence paths and confidence labels are more useful than plain grep for direct/resolved relationships
- the no-caller response for dynamic behavior includes a useful caveat

What hurt:
- project-root detection makes the out-of-box experience nearly useless on this repo despite 65k+ lines of Python
- file coverage can say exact while 24 discovered Python files are absent
- Python import resolution depends heavily on choosing the correct source root; there is no obvious documented custom source-root/PYTHONPATH configuration
- QML is a major code language for MahoOS but is absent from both indexing and unsupported-language coverage reporting
- callback/function-value flow can hide real impact edges

Current assessment:
Code-graph is **useful on the right slice of MahoOS**, especially for direct Python impact analysis. It is not yet trustworthy as a whole-repository map of MahoOS without careful root selection and fallback search.

Next real-world work should compare a small set of actual MahoOS engineering questions using:
1. raw repository search/file reading,
2. code-graph alone,
3. code-graph plus fallback verification,

and measure time, queries/tool calls, completeness and false confidence.