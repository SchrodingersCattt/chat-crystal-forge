# Frontend audit (2026-10-09, follow-up)

This is a live smoke record for the native MatterVis hosts. It is separate
from mocked model tests and does not claim that a real OpenAI endpoint was
available. The follow-up closes the two issues recorded in the first pass:
stale persisted scenes and narrow-window side-panel clipping.

## Browser host

From the repository root, the UI was started with:

```powershell
.\.venv\Scripts\python.exe -c "from chat_crystal_forge.cli import app; app()" ui examples\structures\DAP-4.cif --session .crystalforge\browser-audit --port 8050
```

The process reported `Dash is running on http://127.0.0.1:8050/`. Direct
requests to `/` and `/_dash-layout` returned `200`. The layout contains the
intended three regions:

- `left-panel` (340 px initial width) with the Display, Analysis and Operations
  tabs;
- `center-panel` with `flex: 1 1 auto`, `minWidth: 0`, and the MatterVis graph;
- `mv-extension-panels` (320 px initial width) with the Chat panel.

Both side-panel splitters are present and the center graph is no longer a
separate overlay target. The native-host callback test also passes:

```text
.\.venv\Scripts\python.exe -B -m pytest tests/test_frontends.py::test_native_web_with_chat_returns_layout_and_direct_checks -q
```

That test also checks that MatterVis serves `panel_resize.css` and
`panel_resize.js`. Below the 756 px breakpoint, those assets switch the side
panels to opt-in overlays with accessible Tools and Chat toggle buttons. The
center scene keeps the available width instead of being clipped by the
desktop panel minimum.

Reusing an old session is covered by
`test_native_web_prunes_stale_scene_store`. MatterVis removes scene records
whose structure is no longer in the live catalog, persists the repaired store,
and then registers the current CIF. A stale `viewer.json` therefore no longer
causes an unknown-structure scene to survive into the visible workbench.

## Terminal host

The native TUI integration test passes with the local environment:

```text
.\.venv\Scripts\python.exe -B -m pytest tests/test_frontends.py::test_native_tui_keeps_viewer_and_routes_chat_input -q
```

The test confirms that the MatterVis canvas remains mounted while `/inspect`
is submitted through the Forge Chat input. The test runner needs the normal
desktop socket permissions on Windows; in the restricted sandbox it can fail
before the test starts while creating `asyncio`'s socket pair.

## Closed findings

- MatterVis owns current-frame delivery, hydrogen visibility, camera reset and
  SVG cleanup, so a native viewer change does not leave stale Display controls.
- Analysis and Operations share the left workbench; Chat is the right-side
  extension region. The center scene keeps a readable desktop minimum and
  uses the compact overlay mode on smaller windows.
- Chat keeps its own padding and compact result cards, so the native server-log
  overlay does not hide conversation content.
- MatterVis supplies the right-click inputs and polyhedra-controls wrapper
  covered by its focused regression suite.
- The TUI path still loads without Dash, Flask or Plotly imports; the parent
  subprocess isolation test remains the guard for that boundary.

The in-app browser used for the first pass is isolated from the local loopback
socket, so this record does not claim a new human-visible screenshot. The HTTP
asset checks, native-host tests and MatterVis recovery tests are the
reproducible evidence available in the repository.
