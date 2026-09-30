# Interfaces and visual design

Status: design draft. Both first-release frontends, the same core task journey,
`mat-chat tui` / `mat-chat ui`, the left-structure/right-chat layout, palette families
and Arial/Consolas typography are confirmed. Exact colors and secondary interactions
remain proposals pending review. The approved plan reuses actual native MatterVis
UI/TUI through optional Forge Chat. Only the first read-only slice is active;
completed-app verification is not asserted here.

## Naming and command surface

| Item | Working name / confirmed command spelling |
| --- | --- |
| Repository / distribution | `chat-crystal-forge` |
| Python package | `chat_crystal_forge` |
| Product display name | CrystalForge |
| Executable | `mat-chat` |
| Terminal interface | `mat-chat tui` |
| Browser interface | `mat-chat ui` |

The user selected the symmetric `tui` / `ui` pair. Do not add `start-ui` aliases
without a separate request. These are planned launch commands; successful
installation/startup must be verified by main. Package and
executable availability has not been checked for publication.

TUI starts in the current terminal. UI starts a local browser service, bound to
loopback by default; it must not silently expose a research server on all network
interfaces. Browser auto-opening and optional CLI flags remain to be decided.
Do not require a browser for terminal use or assume a graphical desktop exists.

## Shared interaction

Both frontends must complete the same core journey in the first release: chat,
processing, inspection of check results, decisions on exceptions and export.
The left-structure/right-chat layout and full plan are approved for implementation.
Secondary interactions below remain design guidance. Progress is recorded in the
draft [Checklist](../devpost/checklist.md), not implied by approval.

- The left workspace shows the selected structure, batch navigation and validation
  findings. The right panel shows the conversation, execution progress and requests
  for decisions. Keep the structure view useful rather than replacing it with logs.
- Selecting a finding or an explicit structure/atom reference in chat focuses the
  corresponding structure revision and atoms. A view change does not edit a crystal.
- Distinguish the original, candidate and validated exported result. A temporary
  preview is not a committed scientific operation or evidence of completion.
- Show truthful states for queued, running, awaiting decision, blocked, failed and
  passed work. A finished model message is not a finished batch.
- Keep input scope, selected structure and batch progress visible. Do not rely on
  color alone to communicate status.

Rendering may differ between the frontends, but the TUI is not a log-only client.
The first repair scenarios are disorder and missing hydrogens; see
[Structure preparation](structure-preparation.md) for decisions and delivery rules.

## Browser UI

Reuse MatterVis's actual Dash app, native backend, controls and renderer. Mount
optional Forge Chat through the [Plugin protocol](plugin-protocol.md), not a
replacement viewer built from scene APIs. Keep two panels: structure on the left,
conversation on the right. Resizing is proposed. Batch navigation and check results may
use compact sections within the left workspace; their exact placement is not set.

Use white and light gray for most surfaces. Reserve dark gray, dark blue, dark
teal and crimson for meaningful emphasis. Initial token proposals:

| Role | Proposed value |
| --- | --- |
| Page | `#FFFFFF` |
| Secondary surface | `#F3F4F6` |
| Border | `#D1D5DB` |
| Primary text | `#374151` |
| Primary action / selected item | `#1E3A5F` |
| Passed / confirmed | `#0F615B` |
| Failed / destructive action | `#B91C3C` |

These values are draft design tokens, not contrast-tested combinations. Verify
text/background contrast and keyboard focus in the implemented interface.
Use explicit labels/icons for waiting and errors; avoid decorative status colors,
gradients or a dark dashboard that contradicts the requested light design.

Use `Arial, sans-serif` for prose and interface text, and `Consolas, monospace`
for code, coordinates, identifiers and logs. Allow platform fallback glyphs for
Chinese and other text. Do not bundle proprietary font files without permission.

## Terminal UI

Reuse the actual MatterVis `CrystalTUI` Textual app and native controls with the
optional Forge extension, verified against the selected dependency version.
Do not create a competing viewer/backend. Show structure on the left and chat on
the right when the terminal is wide enough. A keyboard-switchable view is proposed
for narrower terminals, without losing conversation, task state or decisions.

Proposed terminal behaviors include keyboard-only operation, visible focus,
resizing and readable progress while tools execute. Display terminal geometry, not a
promise of browser-equivalent raster rendering.

TUI font family is controlled by the user's terminal, not by the application.
Recommend Consolas or another compatible monospace font; Arial cannot be enforced
inside an SSH terminal. ASCII/monochrome fallbacks are proposed for terminals that
cannot render the preferred Unicode or colors. Apply semantic accents where supported
while preserving readability under the terminal's background and theme.

Both the terminal and browser show structured tool outcomes, not fabricated
assistant progress or private model reasoning. API credentials never appear in
either interface.

## First-slice interaction boundary

`/load`, `/list`, `/inspect`, `/help` are direct local commands; natural language
requires the configured endpoint. Both apps display shared service snapshots with
messages, structures, busy/error and status fields. One background thread performs
real read-only inspection; no repairs, export certification or `finish` tool yet.
MatterVis retains camera/selection/display state. Distinguish source atoms from
displayed copies; before future repairs invalidate scientific evidence on manual
native edits. The minimal host patch is under validation, not published; richer
versioned events are planned rather than implemented.