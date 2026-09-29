# Inspection-preview validation

The first slice is available locally for early feedback, not release-ready.

## Verified

- Parent suite: 44 tests, including actual MCK inspection on synthetic CIFs,
  config/persistence/worker lifecycle, mocked model tool calling, native Web/TUI
  integration, and a subprocess forbidding browser imports on terminal loading.
- Parent Ruff check and wheel build succeeded.
- MatterVis extension/lifecycle, callback-layout, BFDH failure-output and module
  organization subset: 39 tests passed. Its full source Ruff check passed.
- Browser verification: native MatterVis view plus Forge panel, real `/inspect`
  submission and six MCK results displayed. No live model request was made.

## Blocking full regression

Run MatterVis tests from `external/mattervis`; several fixtures use repository-relative
paths. The last full correctly rooted run returned 1172 passed, 48 skipped and one
failure in `tests/perf/test_dap_o4_oracle.py::test_dap4_pipeline_oracle` (before the
last callback/BFDH regressions were added).

That test requires MCK `f2188c1`, while the development source pin is `a271cb7`.
An isolated experiment using the recorded historical MCK/MatterVis source pair
also failed to reproduce the archived report under the available transitive
dependency environment. The original full environment and exact difference need
investigation. No oracle values, skip rules or assertions were changed.

The CI runs the full upstream gate without exclusions. Do not publish a new parent
pin until the upstream commit is reachable and its required validation is resolved.

## Still unverified or unfinished

- Live endpoint/model compatibility; local `.env` configuration is needed.
- User feedback in both interfaces; no hands-on approval has been assumed.
- Live viewer edits/uploads synchronized with Forge input revisions.
- Hydrogen/disorder operations, all-pass completion/export and batch recovery.
- Fresh Linux execution and hosted CI runs.

Inspection targets registered original copies, not arbitrary live viewer state.
Synthetic test inputs are not experimental or benchmark-performance evidence.