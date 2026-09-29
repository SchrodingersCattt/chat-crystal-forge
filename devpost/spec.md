---
doc: spec
status: draft
---

# CrystalForge — Technical Spec

## How This Works, In Plain Language

MatterVis retains its actual structure viewer and controls. Optional Forge Chat
uses one shared service to inspect CIFs through MCK and interpret natural language
through the configured model. Later the service runs authorized repairs, saves
task history and verifies exported files. Neither frontend invents scientific
results, and no replacement viewer or chemistry engine is needed.

## The Core Journey Through the System

PRD ref: `prd.md > The Core Journey`.

1. Typer launches the actual MatterVis UI or TUI with the Forge extension.
2. Input registration retains source identity; MCK inspects without automatic
   disorder resolution.
3. Direct commands execute locally; natural-language turns use the endpoint and
   validated domain tools through the same service.
4. Detached snapshots publish results beside native controls. Slice 1 stops here.
5. Later decisions authorize hydrogen/disorder operations in isolated jobs;
   scientific revisions retain lineage and frozen check policy.
6. Export/reload checks verify actual files; deterministic completion accounts
   for every agreed output and required executed check.

## Stack

| Accepted choice | Role / tradeoff | Documentation |
| --- | --- | --- |
| Python >=3.11 | Shared local core; verify upstream compatibility | https://docs.python.org/3.11/ |
| Typer | Command entry points without another service | https://typer.tiangolo.com/ |
| Official OpenAI Python SDK | Compatible chat/tool requests; actual provider support needs testing | https://github.com/openai/openai-python |
| SQLite | Later local persistence without database hosting | https://www.sqlite.org/docs.html |
| Pinned MolCrysKit | Existing chemistry and sanity criteria | https://github.com/SchrodingersCattt/MolCrysKit |
| Existing MatterVis apps | Native controls and optional host, not rewritten viewers | https://github.com/SchrodingersCattt/MatterVis |
| Dash/Plotly and Textual | Keep native lifecycle and optional browser imports | https://dash.plotly.com/ ; https://textual.textualize.io/ |

Exact installed versions and compatibility require verification against pins. No
extra React/FastAPI layer is planned. Reuse the existing `.venv` as user-selected.

## Where It Runs and How Someone Tries It

Local workstation or SSH terminal; browser service binds to loopback by default.
After installation, planned commands are `mat-chat tui` and `mat-chat ui`. Load a
known CIF, use `/inspect`, then try natural-language inspection with an endpoint
configured locally. Planned first-slice tests after installation are
`python -B -m pytest tests`, using the selected environment's interpreter.
Installation, launch and live endpoint verification are pending evidence here.
The short demo video and public GitHub repository are required submission
materials; deployment is optional. No publishing is performed by this document.

## Look and Feel

PRD ref: `prd.md > Look and Feel`.
Native structure workspace left, optional chat right. Light web surfaces with
dark gray/navy/teal/crimson accents; Arial prose and Consolas technical text.
Exact tokens in `docs/interfaces.md` remain contrast-test proposals. Respect
terminal-controlled fonts; test keyboard focus, narrow layout and readable states.

## Components

### Native Hosts and Forge Plugin

PRD ref: `prd.md > Screens and Layout`.
`plugins.py` mounts Forge Chat into actual native apps. The new minimal upstream
`Extension(name)` uses a namespaced name and hooks `build_web_panel(context)`,
`register_web(app, context)`, `build_tui_panel(context)`,
`on_tui_mount(app, context)`, `on_tui_unmount(app, context)`, `close()`.
Hosts are `create_app(..., *, extensions=())` and
`CrystalTUI(crystal, *, ..., extensions=())`. Context viewer is the same native
backend/app; snapshots are detached. No hot web callback unregister is provided.
The host patch is under validation, not published. Richer versioned commands/events
are future design; see `docs/plugin-protocol.md`.

### Shared Read-only Service

PRD ref: `prd.md > Read-only Inspection and Chat`.
`service.py` exposes `ForgeService(workspace, settings=None, client=None)`,
`add_input(Path)`, `submit(text) -> turnid`, `snapshot()` and `close()`.
Snapshot dictionaries contain `messages`, `structures`, `busy`, `error`, `status`.
One background thread performs first-slice read-only model/MCK work. Serialize
publication and detach snapshots; do not share mutable structures with viewer
callbacks. Verify shutdown/late results without pretending threads can be killed.
`/load`, `/list`, `/inspect`, `/help` are local commands, not AI. No `finish` yet.

### Configuration and Model Adapter

PRD ref: `prd.md > Read-only Inspection and Chat`, `prd.md > States and Boundaries`.
`config.py` loads the intended ignored `.env` with process environment precedence:
`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`. One model/session owner sends
requests from the backend/TUI process, never browser JavaScript. Validate tool
arguments, preserve tool-call/result pairing, redact errors and avoid provider
fallback. File/model content cannot grant arbitrary shell or Python execution.

### MCK Inspection and Preparation Adapter

PRD ref: `prd.md > Hydrogen Completion and Export`,
`prd.md > Disorder Decisions and Delivery Counts`.
`mck.py` adapts verified installed APIs. Start with read-only inspection; later
authorize hydrogen/disorder operations, retain independent formula/moiety and
source-selection records, and export/reload under the same check policy. Existing
MCK criteria plus coverage guards are not a new chemistry validator. Follow
`docs/structure-preparation.md` for ambiguity, modes, counts and limitations.

### Later Jobs and Completion Core

PRD ref: `prd.md > Batch Jobs and Recovery`, `prd.md > All-pass Completion`.
Later isolated processes handle mutating/heavy operations. SQLite stores tasks,
decisions and outcomes. Reject stale results and reconcile interrupted jobs before
resubmission. Completion requires a nonempty batch, all agreed outputs and actual
passing checks on independently reloaded files. Dedicated storage/jobs/policy
modules are planned later, not first-slice implementation claims.

## Data Model

Initially messages, registered structures, busy/error and status are in-memory
service state exposed by detached snapshots. Main must review nested record shapes
and turn lifecycle against implementation. First-slice restart persistence is not
promised. Later SQLite records sessions/turns, inputs, revisions, jobs, events,
decisions, policies, check outcomes and artifact mappings; task-owned revisioned
files preserve originals and exports. Restart exposes unfinished work truthfully.

MatterVis owns native camera/display/selection; Forge owns scientific task state.
Source atom IDs map explicitly to displayed copies. Before future repairs, manual
native scientific edits invalidate affected evidence and advance revision identity;
camera changes do not. Richer viewer events/revision tokens are later contracts.

## File Structure

Planned first-party files; partial existing files do not certify a working slice:

- `src/chat_crystal_forge/cli.py` — Typer launch with native extensions.
- `src/chat_crystal_forge/config.py` — local settings and validation.
- `src/chat_crystal_forge/service.py` — shared chat/inspection state and work.
- `src/chat_crystal_forge/mck.py` — MCK calls and evidence translation.
- `src/chat_crystal_forge/plugins.py` — native UI/TUI panels.
- `tests/` — config/service/MCK/plugin tests and later integration cases.
- `external/molcryskit/`, `external/mattervis/` — pinned upstream sources.
- `docs/` — canonical engineering plan and focused contracts.
- `devpost/` — template-based scope, PRD, spec and checklist.

Main may split modules later as needs become concrete. Generated dependencies and
unimplemented richer core modules are not presented as current code.

## External Services and Dependencies

The official SDK targets the configured API root's chat completions interface with
`model`, `messages` and allowed `tools`, consuming assistant content/tool calls and
returning results paired by tool-call ID. See
https://platform.openai.com/docs/api-reference/chat . Authentication, streaming/tool
support, rate limits and cost depend on the actual endpoint and remain unverified;
do not invent rates or quotas. Keys stay local and only task-relevant data is sent.

MCK/MatterVis are pinned local source dependencies, not remote chemistry services.
Verify import origins. Fix host/native-view bugs in MatterVis, chemistry bugs in
MCK and workflow bugs in Forge, with regression tests in the responsible repo,
reachable upstream commits and then validated parent pins. SQLite is local.

## Important Failure Modes

- **Malformed/ambiguous CIF or incomplete checks** — structured findings and
  blocked/decision state; preserve originals and never substitute a blanket pass.
- **Endpoint/configuration failure** — actionable redacted error; local commands
  remain explicitly local, with no fake natural-language response.
- **Lifecycle race or stale result** — reproduce/test in the owning repository,
  reject obsolete evidence; no sleeps or competing viewer backend.

## What Was Simplified and Why

- One coordinator instead of agent teams keeps task policy and evidence coherent.
- One read-only thread first, isolated mutation jobs later, proves interaction
  before introducing durable heavy-job machinery.
- Native apps instead of rewritten viewers preserve existing capabilities and
  correct bug ownership.
- Adopt concepts from https://learn.shareai.run/zh/ s01/03/07/08/11/12/13, not copied
  shell-agent code. Recovery/task records/compaction mature later; preserve decisions
  outside prompts and impose no invented global time, cost or experiment budget.

## Decisions and Open Issues

Approval evidence: “Start implementation”, 2026-09-29, after the complete
12-section plan. This consolidation stays draft for main review. Existing `.venv`
reuse is confirmed; build mode remains unset pending early feedback. No personal
learning uncertainty or experience was established; none is invented. The concrete
engineering investigation is host compatibility: test native identity, optional
imports, snapshots and cleanup in both apps. Main must confirm nested service
records, install commands and evidence. Endpoint settings and redistributable demo
inputs are still needed. Native-edit invalidation precedes repairs; chemical
choices stay task-specific. No build/test milestone is asserted by this spec.