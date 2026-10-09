# Frontend notes for the final review

This is the public, source-grounded issue log for the native MatterVis hosts and
the Forge Chat extension. It records observations already present in
`docs/validation.md` and `devpost/checklist.md`; it does not turn a mock test or
an agent-only check into learner approval.

## Observed problems and current state

| Area | Observation | Current state / owner |
| --- | --- | --- |
| Display controls | An earlier browser session left stale Display controls after a native viewer change. | MatterVis now owns current-frame delivery, hydrogen visibility, camera reset and SVG cleanup. The native-host regression remains green. **MatterVis** owns the view state. |
| Layout | Four columns crowded the central structure, and the old right-panel heading was misleading. | Analysis and Operations open in the left workbench; Chat is the right-side extension region. At widths below 756 px, MatterVis switches both side panels to accessible overlays. **MatterVis** owns generic layout; **Forge** owns chat content. |
| Reused sessions | A previous `viewer.json` could retain a scene for a structure that was no longer loaded. | MatterVis prunes unknown scene records during startup and persists the repaired store. The parent has a recovery regression for this path. **MatterVis** owns scene state. |
| Chat result area | Chat padding could be hidden by the native log overlay; result cards were difficult to scan. | The current panel keeps its own padding and compact result cards. Parent presentation tests cover the visible labels and raw-result disclosure. **Forge** owns the panel presentation. |
| Browser controls | Earlier validation found missing right-click inputs and a missing polyhedra-controls wrapper. | The focused MatterVis regression suite covers both controls. **MatterVis** owns these controls. |
| Terminal startup | The TUI must stay usable without importing Dash/Flask/Plotly. | The parent subprocess import-isolation test remains green, and the native TUI routes `/inspect` through the shared service. **Forge + MatterVis** share the integration boundary. |

## Evidence for the final review

The reproducible follow-up commands are in `docs/frontend-audit.md`. They cover
the HTTP layout and responsive assets, stale-scene recovery, Chat presentation,
and the TUI input route. Learner hands-on approval remains a separate checklist
item and is not inferred from these automated checks.

If a problem belongs to the generic viewer, add a focused regression in
`external/mattervis` first; if it changes workflow evidence or completion policy,
change the shared Forge service and its tests. Do not paper over a race with a
sleep or duplicate view state.
