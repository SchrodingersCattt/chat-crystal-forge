---
doc: checklist
status: draft
---

# Build Checklist

Build mode: unset — pending early first-slice feedback; no preference inferred.

Approval evidence: “Start implementation” on 2026-09-29 followed the complete
12-section plan. Slices 1–5 are implemented in the shared service and both native
frontends. Hands-on review and the learning wrap-up below are still open.

These three items are outside the submission: HTTP routes for hydrogen, disorder,
export and finish; invalidating evidence after a native viewer edit; applying one
disorder choice automatically to later structures.

## Slices

- [x] **1. Inspect real CIFs through optional chat in native MatterVis UI/TUI**
  Becomes usable: Native apps retain their controls while Forge Chat shows shared read-only MCK findings and real endpoint-backed conversation.
  Why now: Proves host/service/chemistry integration without exposing mutation.
  PRD ref: `prd.md > The Core Journey` (steps 1–2), `prd.md > Read-only Inspection and Chat`
  Spec ref: `spec.md > Native Hosts and Forge Plugin`, `spec.md > Shared Read-only Service`, `spec.md > File Structure`
  Build: Reuse .venv; install/verify pinned dependencies; wire Typer/config, minimal native host and Forge plugin, one read-only background thread and shared service; expose /load, /list, /inspect, /help; no repairs or finish.
  Verify (mechanical): After installation run planned `python -B -m pytest tests`; verify native apps with/without plugin, same viewer identity, detached snapshots, real MCK calls, unchanged inputs, invalid CIF/config/endpoint errors, responsiveness, cleanup and TUI without optional browser imports. Distinguish mocks from live endpoint trials; no run is claimed here.
  Learner check: Open both apps, load and inspect a CIF, move/select in the native viewer and try chat; report clarity/usability and choose build mode from this early feedback.
  Commit: `Add native Forge Chat and read-only inspection slice`

- [x] **2. Complete hydrogens and retrieve reloaded, checked CIFs**
  Becomes usable: Authorized hydrogen completion yields candidates, records and independently reloaded export checks.
  Why now: Establishes one repair and the export evidence boundary before branching.
  PRD ref: `prd.md > Hydrogen Completion and Export`
  Spec ref: `spec.md > MCK Inspection and Preparation Adapter`, `spec.md > Data Model`
  Build: Add isolated mutation execution, lineage, independent references, ambiguity handling and strict export/reload; establish native-edit invalidation before accepting repair evidence.
  Verify (mechanical): Test H-free/partial-H inputs, ambiguous placement/moiety, warnings, skipped checks, missing/corrupt exports and stale evidence after edits in both frontend paths.
  Learner check: Request hydrogen completion; compare original/candidate and exported-file checks, including a blocked case.
  Commit: `Add hydrogen completion and strict export reload`

- [x] **3. Resolve disorder with explicit strategy and delivery counts**
  Becomes usable: Users select unresolved modes/counts and review actual output selections and warnings.
  Why now: Adds scientific branching to the verified revision/export path.
  PRD ref: `prd.md > Disorder Decisions and Delivery Counts`
  Spec ref: `spec.md > MCK Inspection and Preparation Adapter`, `spec.md > Data Model`
  Build: Adapt optimal/random/enumerate, requested counts, seeds/coupling and selection provenance; preserve explicit choices and report unknown totals, shortages and duplicates.
  Verify (mechanical): Test modes, omitted versus explicit choices, duplicate/short outputs, no automatic input resolution and preserved formula/moiety references through export.
  Learner check: Try unspecified and explicit mode/count requests; check questions and delivered records against intent.
  Commit: `Add explicit disorder delivery decisions`

- [x] **4. Track batches and recover persisted jobs**
  Becomes usable: Inputs, decisions, revisions and outcomes survive restart with interrupted work exposed.
  Why now: Extends verified individual operations to durable batch coordination.
  PRD ref: `prd.md > Batch Jobs and Recovery`
  Spec ref: `spec.md > Later Jobs and Completion Core`, `spec.md > Data Model`
  Build: Add SQLite records and revisioned artifacts, isolated heavy jobs, safe publication, interruption reconciliation and evidence-based no-progress handling.
  Verify (mechanical): Test restart during work, duplicate-submission prevention, stale results, mixed failures and restored input/decision/output mappings.
  Learner check: Run a mixed batch, restart during work and confirm every input has truthful recoverable state.
  Commit: `Add persistent batch jobs and recovery`

- [x] **5. Enforce all-pass completion in both frontends**
  Becomes usable: Shared completion certifies only fully accounted-for, reloaded and checked delivery sets; failures remain visible.
  Why now: Exercises the full journey after repairs and durable evidence exist.
  PRD ref: `prd.md > All-pass Completion`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Later Jobs and Completion Core`, `spec.md > Important Failure Modes`
  Build: Add deterministic finish gating and integrated success/blocked/failed/interrupted presentation without separate frontend policies.
  Verify (mechanical): Test empty batches/checks, skipped/missing results, exceptions, partial batches, stale policy/revisions, corrupt exports and native edits; require real complete delivery evidence and frontend agreement.
  Learner check: Compare a passing batch with one unresolved input; verify the latter cannot claim whole-batch completion in either app.
  Commit: `Enforce shared all-pass completion and failure parity`

- [ ] **6. Verify installation, document the demo and complete final review**
  Becomes usable: Another user can install pinned sources, configure locally and reproduce the documented workflow/demo.
  Why now: Release instructions and claims must follow verified behavior.
  PRD ref: `prd.md > What We're Building`, `prd.md > Open Questions`
  Spec ref: `spec.md > Where It Runs and How Someone Tries It`, `spec.md > External Services and Dependencies`
  Build: Verify installation/start instructions, prepare authorized demo inputs and docs/video plan, resolve final feedback and prepare learning wrap-up/app map from finished code.
  Verify (mechanical): Exercise documented install/start/test paths, both apps and a real endpoint; verify permissions, notices and reachable upstream pins before completion claims.
  Learner check: Follow instructions, explore normal/awkward cases, retry agreed revisions and explicitly confirm readiness.
  Commit: `Document verified installation and reviewed demo workflow`

## Hands-on Checkpoints

- [ ] Early usable behavior explored — after slice 1, including native viewer/chat feedback and build-mode choice
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: Not yet performed; no test or hands-on completion recorded.
Route and stops: Not yet selected from finished code.
Edit outcome: Not yet offered or performed.
Reflection: Not yet offered; no personal answer inferred.
Activity mode: Unset pending actual activity and feedback.

## Revisions

- User hands-on feedback identified stale Display controls, four-column crowding,
  and the wrong right-panel heading. MatterVis now owns the left-tab workbench,
  current-frame delivery, explicit hydrogen visibility, camera reset and SVG
  cleanup fixes. Forge's panel is titled Chat and has compact result cards. This
  is early review feedback; later repair/export slices are still not complete.

- The first preview uses one background thread for read-only tools; process-based
  mutation and full recovery remain later slices. Native uploads/edits are not yet
  synchronized with Forge's registered input copies and are explicitly labeled.
- Validation: 43 parent tests passed before the added browser-import isolation
  test. Native extension and callback-layout regression subset: 37 passed.
  Full MatterVis run: 1172 passed, 48 skipped, one failure in the existing
  `test_dap4_pipeline_oracle` dependency-locked oracle. No check was weakened.
- The archival oracle also differed when executed with its recorded historical
  MatterVis/MCK source pair under the available dependency environment. Its exact
  numerical/dependency baseline remains unresolved; do not mark full regression
  or release readiness complete. The new CI preserves this failing gate.
- Browser validation found existing missing right-click inputs and a missing
  polyhedra-controls wrapper. The fix and regression tests belong to MatterVis.
  After restart, an actual browser click on Send with `/inspect` displayed all six
  MCK results for the synthetic water input. Chat padding avoids the native log
  overlay. No live LLM was tested because endpoint/model configuration is absent.
- Latest parent validation: 44 tests passed, including native-host integration and
  a subprocess rejecting Dash/Flask/Plotly imports on the TUI loading path. Wheel
  build succeeded. Upstream focused tests passed (39), and both Ruff checks passed.
  The full upstream oracle failure remains a release/push blocker; these counts
  do not imply a passing full suite or completed first-slice hands-on review.