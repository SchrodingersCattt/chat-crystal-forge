# Frontend audit (2026-10-09)

This is a live smoke record for the native MatterVis hosts. It is separate
from the mocked model tests and does not claim that a real OpenAI endpoint was
available.

## Browser host

From the repository root, the UI was started with:

```powershell
.\.venv\Scripts\python.exe -c "from chat_crystal_forge.cli import app; app()" ui examples\structures\DAP-4.cif --session .crystalforge\browser-audit --port 8050
```

The process reported `Dash is running on http://127.0.0.1:8050/`. A direct
HTTP request to `/` and `/_dash-layout` returned `200`. The layout contains the
intended three regions:

- `left-panel` (340 px initial width) with the Display, Analysis and Operations
  tabs;
- `center-panel` with `flex: 1 1 auto`, `minWidth: 0`, and the MatterVis graph;
- `mv-extension-panels` (320 px initial width) with the Chat panel.

Both side panel splitters are present and the center graph is no longer a
separate overlay target. The existing native-host callback test also passed:

```text
pytest tests/test_frontends.py::test_native_web_with_chat_returns_layout_and_direct_checks -q
1 passed
```

When reusing an old session, MatterVis logged one dropped scene that referred
to an unknown structure. It did not prevent the page from serving, but it is a
useful signal that a stale `viewer.json` can retain scene state after inputs
change. For a demo, use a fresh session directory (or intentionally explain
the recovery behavior). A future polish fix could prune stale scenes when the
session's registered structure set changes.

## Terminal host

The native TUI integration test passed with the local environment:

```text
pytest tests/test_frontends.py::test_native_tui_keeps_viewer_and_routes_chat_input -q
1 passed
```

The test confirms that the MatterVis canvas remains mounted while `/inspect`
is submitted through the Forge Chat input. The test runner needs the normal
desktop socket permissions on Windows; in the restricted sandbox it can fail
before the test starts while creating `asyncio`'s socket pair.

## Open frontend issue to discuss

The current resize script guarantees a 420 px minimum center scene and clamps
each side panel to at least 160 px when the available width is exhausted. The
minimum combined width is therefore about 756 px (160 + 8 + 420 + 8 + 160).
Below that viewport width, `#viewer-root` keeps `overflow: hidden`, so a very
narrow browser window can clip part of the workbench even though the panels do
not overlap the center graph. This needs a product decision:

1. add a responsive collapse/overlay mode for one or both side panels;
2. allow the center scene to shrink below 420 px; or
3. keep the current desktop-first behavior and document the minimum supported
   window size.

No change was made for this item because it changes the approved interaction
model. The default desktop layout and panel resizing are currently covered by
the native layout test.

The in-app browser provided to this sub-agent is isolated from the local
loopback socket, so a final human-visible screenshot still needs to be taken
from the main desktop task. The HTTP and native-host checks above are the
reproducible evidence available here.
