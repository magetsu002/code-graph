# Code Graph Review

Tested against commit `05542ba9132d21cc404930a9d0aa410bfba723de`.

I tested Code Graph with small controlled cases first, then used it on MahoOS as a real project. I wanted to see where it was actually useful, where it missed things, and whether the output made those limits clear.

## Overall

I do think Code Graph is useful.

The strongest part for me was impact analysis. On MahoOS it found transitive callers and dependency chains that would have taken several normal searches to reconstruct manually.

The main weakness I found is trust around incomplete results. Positive results were usually useful because they came with concrete paths and confidence labels. Negative or partial results were where I had to be more careful.

## What worked well

Impact and reachability were useful when the code stayed inside a supported language and the project root matched the way the code is imported.

The confidence labels also helped. Exact, resolved and heuristic edges were meaningfully different in the tests I ran.

Ambiguous Python method calls did not invent fake relationships. In cases where a call could not be resolved, Code Graph was generally conservative.

Indexing was also fast enough that performance did not feel like a problem during normal use.

## Issues I found

### Coverage can look complete when some Python files are missing

I reproduced this in controlled cases and then hit it naturally on MahoOS.

One run discovered 288 Python files, but only 264 became indexed modules. Coverage still reported `python 288 exact` and said every source file was indexed.

Parse failures and oversized skipped files can cause the same problem.

I think parser mode and file completeness should be reported separately.

### TypeScript cache can return stale relationships

The TypeScript facts cache can be reused when the file contents changed but the size and modification time stayed the same.

I changed a call from `foo()` to `bar()`, kept the same byte length, restored the old modification time, then re-indexed.

The cache hit and the graph still returned the old `run -> foo` relationship as exact.

The cache fingerprint should include source content or use another invalidation method that cannot return old semantic data for new source.

### Partial framework results can look complete

I tested two documented limitations.

A NestJS route wrapped through `applyDecorators(Get(...))` was missed.

A Django route created inside a helper function was also missed.

Missing those is understandable because both cases are already documented as limitations. The problem is that the route query still returned output like `all routes: 1 of 1 routes` without making it clear that another real route could be outside the graph.

This is the biggest trust issue for me. A non-empty partial answer can look exhaustive.

### Python project root detection is restrictive

MahoOS has a large Python codebase, but indexing the repository root initially indexed none of the Python because there was no root Python project marker.

Indexing the `lib` directory directly worked much better.

A configurable Python source root would help projects that do not use a conventional package layout.

### Callback flows can disappear from impact analysis

MahoOS has code that stores several policy functions in a tuple and calls them through a loop variable.

`network_proposals` is definitely used at runtime, but Code Graph records no caller for it.

Even if following the full callback is difficult, a function reference edge would still make the impact result more useful.

### Normal Python script entry points are not treated as entry points

A regular pattern like this:

```python
if __name__ == "__main__":
    main()
```

still results in `entry points: 0`.

Calls made inside `main()` are indexed correctly, so this looks like an entry point modelling gap rather than a parsing problem.

### Python tests are not represented by the tests feature

MahoOS has direct pytest coverage for functions I queried, but `cg tests` returned zero test cases because the Python tests were not represented as test nodes.

Supporting normal pytest layouts such as `tests/test_*.py` would make this feature much more useful for Python projects.

### Unsupported source types should still appear in coverage

MahoOS contains a large amount of QML and shell code.

Those files are important to the system, but they are not clearly represented in the coverage summary.

Even if a language is unsupported, I would rather see something like `qml: 113 unsupported` than have it silently disappear from the coverage picture.

## Real project experience

The best real example was `plan_runtime_recovery`.

A normal text search found the six direct production call sites. Code Graph found those same callers and also showed the transitive callers above them with evidence paths.

That was genuinely helpful.

`evaluate_admission` was another good example. A basic search only exposed the immediate call site, while Code Graph traced the dependency chain through several update and admission paths.

That is where I would use Code Graph first.

On the other hand, I would still fall back to normal search when Code Graph says there is no path, no caller, or no test coverage. Those answers can be affected by callbacks, project layout, unsupported languages, entry point modelling and framework behaviour.

## What I would change first

If I had to prioritize the improvements, I would start with completeness reporting.

The graph does not need to understand every dynamic behaviour. It just needs to be very clear about what the current answer actually covers.

After that, I would work on source root configuration, Python tests, Python script entry points and function reference flows.

## Final thought

I would use Code Graph as an accelerator for structural navigation, especially impact analysis.

I would not use it as the only source of truth for proving that something has no callers, no path or no coverage yet.

The positive graph evidence is the strongest part of the tool. The next step is making the boundaries around incomplete evidence just as clear.
