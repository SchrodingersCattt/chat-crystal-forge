# Frontend notes for the final review

This is the public, source-grounded issue log for the native MatterVis hosts and
the Forge Chat extension. It records observations already present in
`docs/validation.md` and `devpost/checklist.md`; it does not turn a mock test or
an agent-only check into learner approval.

## Observed problems and current state

| Area | Observation | Current state / owner |
| --- | --- | --- |
| Display controls | An earlier browser session left stale Display controls after a native viewer change. | The fix moved current-frame delivery, hydrogen visibility, camera reset, and SVG cleanup into MatterVis. Recheck after the final server restart. **MatterVis** owns the view state. |
| Layout | Four columns crowded the central structure, and the old right-panel heading was misleading. | Analysis and Operations now open in the left workbench; Chat is the right-side extension region. The app-map and checklist describe the intended shape. Recheck at the target viewport. **MatterVis** owns generic layout; **Forge** owns chat content. |
| Chat result area | Chat padding could be hidden by the native log overlay; result cards were difficult to scan. | The padding and compact result cards are in the current parent history. Check the browser with `/inspect` and a blocked result. **Forge** owns the panel presentation. |
| Browser controls | Earlier validation found missing right-click inputs and a missing polyhedra-controls wrapper. | The regression fix belongs to MatterVis and is recorded in the upstream-focused validation. Verify the controls in a fresh UI process. **MatterVis** owns these controls. |
| Terminal startup | The TUI must stay usable without importing Dash/Flask/Plotly. | The parent test suite includes a subprocess import-isolation check. A real TUI pass through `/complete-h`, `/disorder`, `/export`, and `/finish` remains a release task. **Forge + MatterVis** share the integration boundary. |

## What to discuss while the service is running

1. Is the central structure still readable at the demo viewport while Chat is
   open, and which panel should collapse first when space is tight?
2. Does each result card make the next decision obvious (formula reference,
   disorder count, export, or blocked reason)?
3. Should a blocked `/finish` result link to the exact missing export/check, or
   is the current reason text sufficient for the demo?

The next review should capture the exact command, viewport, and observed result.
If a problem belongs to the generic viewer, add a focused regression in
`external/mattervis` first; if it changes workflow evidence or completion policy,
change the shared Forge service and its tests. Do not paper over a race with a
sleep or duplicate view state.
