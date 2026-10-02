# M4 framework completeness — partial-result trust failure

Evaluated upstream commit: `05542ba9132d21cc404930a9d0aa410bfba723de`

This milestone targets the original false-confidence question directly: can a query return a clean, non-empty partial answer while an unsupported framework mechanism silently hides another real relationship?

Two documented framework limitations reproduce that behavior.

## CG-T003 — non-empty route queries can look exhaustive across known semantic gaps

Severity: **Medium/High trust design issue**

This is not a claim that code-graph must statically solve every framework abstraction. Both misses below are documented limitations. The problem is how those limitations are communicated at query time.

### T07 — NestJS custom route decorator

Fixture:
`torture/fixtures/typescript/nest-custom-decorator`

Source contains two real Nest routes in one controller:
- direct `@Get("direct")`
- local `@WrappedGet("wrapped")`, implemented through `applyDecorators(Get(path))`

Observed graph:
- `GET /users/direct` is indexed exactly.
- `GET /users/wrapped` is absent.
- TypeScript coverage reports `exact`.
- MCP `routes()` reports `all routes: 1 of 1 routes` with no completeness caveat.

The omission itself is documented in `docs/limitations.md:56` and `docs/ts-frameworks.md:107-108`.

### T08 — Django URL generated inside a function

Fixture:
`torture/fixtures/python/django-dynamic-url`

Source contains:
- a direct `path("direct/", ...)`
- a second `path("generated/", ...)` returned by `build_extra_routes()` and appended to `urlpatterns`

Observed graph:
- `ANY /direct/` is indexed exactly.
- `ANY /generated/` is absent.
- Python coverage reports `exact`.
- MCP `routes()` again reports `all routes: 1 of 1 routes` with no completeness caveat.

This limitation is documented in `docs/limitations.md:98`: URL confs built in loops/functions are only partly resolved.

## Why this matters

These are stronger false-confidence examples than an empty query.

The agent receives a plausible non-empty answer:
`all routes: 1 of 1 routes`

There is no obvious reason to fall back to grep/file reading, even though the tool's own documentation already knows classes of route construction that it does not model.

The current MCP wrapper adds coverage notes only when output matches an `EMPTY_MARKERS` string (`codegraph/mcp_server.py:108-132`). Partial non-empty results therefore receive no coverage note. Even if the normal language coverage note were appended, it would still say the files are exactly covered; file coverage and framework-semantic coverage are different dimensions.

## Suggested direction

Do not solve this by printing the entire limitations document after every query.

Instead, expose compact query-relevant capability metadata, for example:

```text
routes: 1 recorded
completeness: partial
known unmodelled mechanisms detected:
- Nest local decorator WrappedGet -> applyDecorators(Get(...))
```

or, where the unsupported construct cannot be detected:

```text
routes: 1 recorded
scope: statically recognised route mechanisms only
known framework limitations: custom Nest route decorators; dynamic Django URL construction
```

A structured MCP response could separate:
- file coverage
- parser/indexing success
- semantic/framework capability
- unresolved constructs encountered
- whether the result is intended to be exhaustive

That would preserve useful partial answers without teaching an agent to interpret `1 of 1` as ground truth about the application.

Machine-readable output: `m4-framework-completeness.json`.