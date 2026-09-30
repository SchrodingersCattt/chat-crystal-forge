---
doc: prd
status: draft
---

# CrystalForge — Product Requirements

Conversational experimental-CIF preparation for wet-lab researchers.
Source: `scope.md > The Unique Kernel`, `scope.md > The POC Boundary`.

## The Core Journey

1. Open the native MatterVis browser or terminal application with Forge Chat.
2. Load experimental CIF inputs and inspect their structures and actual findings.
3. Describe the preparation; review the supported action and resolve missing
   scientific choices, including disorder delivery mode/count.
4. Follow real operations and checks; inspect results without changing scientific
   data merely by moving the camera or selecting atoms.
5. Resolve consequential warnings or see why work is blocked. Resume interrupted
   work without losing originals or disguising incomplete execution.
6. Retrieve every input's agreed CIF delivery set and operation/check records.
   Success requires independent reload and all required checks actually passing.

Slice 1 covers steps 1–2 and read-only conversation only.

## Screens and Layout

Use actual MatterVis Dash UI and Textual TUI, with native structure controls on
the left and optional Forge Chat on the right. Do not create replacement viewers.
Both frontends present the same task findings and decisions; terminal use works
over SSH without starting a browser service. Narrow-terminal adaptation remains
an implementation detail to validate in early feedback.

## Look and Feel

White/light-gray browser surfaces; dark gray, navy, dark teal and crimson accents.
Arial prose, Consolas technical values, platform fallbacks; terminal font remains
terminal-controlled. Labels communicate status without reliance on color. Preserve
native viewer usability rather than replacing it with logs.

## Features and Behavior

### Read-only Inspection and Chat

Source: `scope.md > The Core Loop`.
Register inputs without modifying originals. `/load`, `/list`, `/inspect`, `/help`
are visible local commands, not simulated AI. Natural-language requests require
a configured endpoint; missing settings produce actionable feedback. Show actual
MCK findings, errors and coverage limits, with responsive native controls.

- [ ] Both native frontends show real inspection outcomes and remain usable.
- [ ] Invalid input and endpoint failure are visible; no repair or finish action
  is offered by the first slice.

### Hydrogen Completion and Export

Apply MCK completion to H-free and partial-H inputs when scientific choices are
clear. Ask about ambiguous moiety, charge, protonation or sites. Preserve formula
references and operation lineage. Export the candidate, reload the actual file
and rerun the same checks; errors or missing checks prevent certification.

### Disorder Decisions and Delivery Counts

Ask for unresolved `optimal`, `random` or `enumerate` strategy and desired count.
Apply explicit compatible batch choices without repeatedly asking. Explain that
`optimal` is not energetic optimization. Retain seeds/coupling decisions and report
requested, returned and distinct-selection counts. Unknown totals, shortages and
duplicates remain explicit; never silently generate every replica.

### Batch Jobs and Recovery

Keep every declared input visible alongside its state and agreed outputs. Preserve
originals, decisions and real outcomes across restart once persistence is added.
Interrupted jobs remain interrupted until reconciled; avoid duplicate mutation.
Show no-progress and blocked cases with the evidence needed for the next decision.

### All-pass Completion

Source: `scope.md > What "Working" Looks Like`.
Only a nonempty batch with all agreed outputs and executed passing checks can
finish. An empty/skipped report, missing prerequisite, exception or stale result
is not success. Requested repairs need evidence beyond a sanity boolean. Policy
changes or manual scientific edits invalidate affected prior evidence. All-pass
refers to the selected delivery set, not all theoretical disorder replicas.

## States and Boundaries

- **Empty** — invite input; do not present an empty task as complete.
- **Inspecting / running** — show real busy state while native controls remain usable.
- **Awaiting decision / blocked** — explain missing scientific choice or evidence.
- **Failed / interrupted / cancelled** — preserve findings and originals; do not
  label these successful. Durable recovery is a later slice.
- **Inspected** — read-only results exist; this is not repaired or export-validated.
- **Passed** — reserved for the declared checked result; batch completion is gated.
- **Restart** — later persisted tasks restore provenance, not an assumption that
  in-flight work finished. Slice 1 does not promise persistence.
- **Privacy** — keys stay local to the requesting process; browser and task records
  contain no credentials. Only task-relevant content goes to the selected endpoint.

## Product Decisions

Actual MatterVis frontend reuse, both-interface parity, current MCK criteria,
MIT licensing and `mat-chat ui` / `mat-chat tui` are confirmed. The user approved
proceeding with the full plan by “Start implementation” on 2026-09-29. Draft
frontmatter awaits main's review of this consolidation, not renewed user consent.

## What We're Building

The six slices in `checklist.md`: native optional chat/inspection; hydrogen and
export; disorder choices; batch persistence/recovery; integrated all-pass gates;
verified install, docs/demo and final user review. Only the first is active.

## Deferred From the POC

Hosted collaboration, scheduled autonomous work and multi-agent teams are deferred
because the local single-coordinator journey establishes the product's kernel.

## Possible Later Enhancements

Additional MCK operations and richer viewer command/event capabilities may extend
the verified core after a concrete use case establishes their need.

## Non-Goals

No new chemistry validator, rewritten renderer, energy optimization, calculation
deck generation or compute submission. No claim that hydrogen presence proves
complete protonation, or that element-set consistency proves exact stoichiometry.

## Open Questions

- Before live-model verification: supply endpoint/model settings locally.
- Before public demo: identify representative inputs and redistribution permission.
- During slice 1: validate minimal host compatibility and usability; obtain early
  feedback and select build mode. No preference is inferred.
- Before future repairs: verify native-edit invalidation and scientific revision
  mapping; task-specific chemical decisions stay runtime questions.