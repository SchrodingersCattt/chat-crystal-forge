# CrystalForge validation

The first slice is available locally for early feedback, not release-ready.

## Verified

- Preparation workflow: DAP-4 ambiguity stops at `awaiting_decision`; confirmed
  formula enables isolated hydrogen completion, bounded disorder generation,
  independent six-check export reload and a code-owned passing `finish` gate.
- Workflow tests cover formula decisions, subprocess jobs, requested/returned
  disorder counts, export evidence and restart interruption. The original DAP-4
  input remains byte-for-byte unchanged.
- `ruff check src tests` and Python syntax compilation pass. The standalone API
  snapshot omits local filesystem paths for structures, revisions and exports.

- Latest parent suite: 54 tests, including actual MCK inspection on synthetic CIFs,
  config/persistence/worker lifecycle, mocked model tool calling, native Web/TUI
  integration, and a subprocess forbidding browser imports on terminal loading.
- Parent Ruff check and wheel build succeeded.
- MatterVis extension/lifecycle, callback-layout, BFDH failure-output and module
  organization subset: 39 tests passed. Its full source Ruff check passed.
- Browser verification: native MatterVis view plus Forge panel, real `/inspect`
  submission and six MCK results displayed. The configured OpenAI-compatible
  endpoint also completed a natural-language inspection of the bundled synthetic
  water input with real `list_structures` and `inspect_structure` tool calls;
  the experimental DAP-4 file was not sent to that endpoint.

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

## Cartesian aspect correction

A live browser inspection reproduced flattened water meshes: final range spans
were approximately `(2.02, 1.76, 0.84)`, but automatic Plotly aspect produced
per-unit scales `(0.87189, 0.81889, 0.46900)`. The Z scale was about 54% of X.
Mesh vertex extents and canvas dimensions did not explain this anisotropy.

MatterVis now derives manual aspect from final padded ranges in all main display
modes, and uses the same normalization for the compass. It preserves mesh vertices,
axis endpoints and explicit camera settings. Browser verification after server
restart, restoring the existing camera, measured equal scales of approximately
`(0.49505, 0.49505, 0.49505)` without a frontend-only aspect override.

The new regression file initially failed 11 cases. After the fix, the focused
aspect/camera suite passed 36 tests (10 existing fixture-dependent skips); the
parent suite passed all 44 tests. Full MatterVis regression: 1204 passed, 48 skipped,
with only the same dependency-locked DAP-4 oracle failure. No oracle expectation
or assertion was changed, and publishing remains blocked on that earlier issue.

## Workbench and Display controls

### Follow-up: apparent resets and stalled delivery

The resumed browser investigation reproduced a separate delivery delay: a water
frame built in 31 ms was not returned by the HTTP fallback until roughly 20 s
later. The fallback interval was 30 s, and WebSocket startup abandoned connection
when Dash had not loaded Plotly yet. Startup now waits for Plotly; HTTP fallback
polls at 500 ms. A Node regression executes the actual startup with Plotly initially
absent, then checks connection and subscription.

The graph no longer sits inside a Dash Loading wrapper: background requests retain
the last valid frame rather than hide the viewer. Polling does not change the
browser title. Full-frame delivery is serialized and deduplicated across Dash and
WebSocket, preserving the live camera for unchanged scene/view revisions.

Live verification after restart: Axes off completed in about 778 ms including
automation overhead, removed the SVG arrows, and emitted one afterplot event.
The rotated camera eye remained (1.6, 0.4, 0.8), within floating-point precision.
Hydrogens off followed by Labels and Axes on converged to revision 4, one oxygen
mesh (70 vertices), one label and no bond geometry, retaining that camera.
Axes still delivers a complete frame; metadata-only overlay delivery remains
separate work, not a completed optimization.

Follow-up full MatterVis run: 1272 passed, 48 skipped, two failures. One was the
known MCK oracle version lock; the other was a layout test still expecting the
removed Loading wrapper. Its replacement asserts the graph directly fills the
center panel, and the seven targeted layout/startup tests then passed. The whole
suite has not been rerun after that assertion update. Forge: 49 passed; source
Ruff and both repository whitespace checks passed.

### Earlier synchronization checks

User feedback reproduced a real state/figure mismatch: `display_options` reached
the backend and advanced render revision to 18, while the browser stayed at 15.
The fast trace patch did not carry a verified geometry base or matching metadata.
Visual-control changes now request current full frames through the existing async
worker and caches. WebSocket delivery no longer advances beyond unsent events;
worker errors clear pending state and emit an observable error.

Further real-geometry/browser checks found and corrected two independent issues:
an explicit `show_hydrogen=False` was overridden by a true preset, and removing
compass metadata left the old SVG arrows on screen. Camera reset also now survives
scene-state reconstruction instead of reviving a creation-time camera.

Browser checks verified H removal produces one oxygen mesh and no bond meshes,
labels appear, disorder-only filters the ordered water view empty, and cell boundary
adds/removes its trace in Unit cell scope. Analysis and Operations open inside the
left sidebar; Chat is the only right-side extension region. Final SVG/availability
verification follows the last server restart.

Full upstream regression after these changes: 1265 passed, 48 skipped, with the
same historical dependency-locked oracle failure. A timer-granularity test was
made deterministic with an injected monotonic clock and an exact duration check,
not skipped or converted to an expected failure. Forge's current suite passed 49
tests using Python stream capture; one earlier run encountered a non-reproduced
Textual/Windows output-handle failure during teardown and is retained as a
portability observation, not claimed fixed by the Web changes.

## Outstanding work

- DAP-4 live endpoint/model compatibility remains unverified because the
  experimental CIF stayed local; the bundled synthetic input passed a live
  natural-language tool-call check with the configured `.env`.
- User feedback in both interfaces; no hands-on approval has been assumed.
- Live viewer edits/uploads synchronized with Forge input revisions.
- Fresh Linux execution and hosted CI runs.
- MatterVis focused tests could not create their default Windows `tmp_path` in
  this sandbox; this is an environment permission failure, not an assertion
  result. The full upstream oracle remains separately dependency-locked.

Inspection targets registered original copies, not arbitrary live viewer state.
Synthetic test inputs are not experimental or benchmark-performance evidence.

## Clean-checkout install and terminal workflow (2026-10-09)

On Windows, a fresh clone from `main` was created under `_tmp/clean-checkout-20261009`
and initialized with the README command `git submodule update --init` (exit code
0). Both recorded submodules were at the parent pins (`MatterVis
e2b3f7a8977d3f9a90cef79fedac1ec85c5280a0`, `MolCrysKit
f2188c14e245b87d99dc1d13ab72e37993d972b0`). In a new Python 3.12 virtual
environment, the README
command completed successfully:

```text
python -m pip install -e external/molcryskit -e "external/mattervis[all,test]" -e ".[dev]"
```

Editable imports (`chat_crystal_forge`, `molcrys_kit`, `mat_viewer`) and
`mat-chat --help` then succeeded. The `mat-chat tui ... --session ...` host
also started successfully. Because this Windows PTY cannot inject Textual
keystrokes reliably, the command chain below was exercised through the same
Forge chat `submit()` path used by the TUI and verified from SQLite after every
turn; this is a protocol check, not a claim of visual or learner acceptance:
`/inspect`, `/complete-h`, `/disorder`, `/export`, `/finish`.

| input | observed result |
| --- | --- |
| `/inspect` | report recorded; source remains unresolved (`blocked` because the `?` formula is not a decision) |
| `/complete-h <id>` | `awaiting_decision` (`formula_reference_required`) |
| `/complete-h <id> C6 H18 Cl3 N3 O12` | `done`, isolated hydrogen revision, 176 H atoms |
| `/disorder <id> optimal 1` | `done`, requested/returned 1, distinct 1, duplicate 0 |
| `/export <id> C6 H18 Cl3 N3 O12` | `done`, reloaded export with all required checks passing |
| `/finish` | `passed`, all declared inputs had independently reloaded passing exports |

The original DAP-4 file was unchanged. The clean checkout and its session are
temporary validation artifacts under ignored `_tmp/` and `.crystalforge/`
paths; they are not part of the deliverable.
