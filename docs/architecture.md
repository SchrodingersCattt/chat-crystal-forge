# Architecture and workflow

Status: engineering draft. The user has requested the shared agentic workflow,
MCK/MatterVis reuse, and the same core task journey in both first-release frontends.
MIT licensing and `mat-chat tui` / `mat-chat ui` are confirmed. Concrete repair scope,
delivery and acceptance are now defined in [Structure preparation](structure-preparation.md):
disorder and missing hydrogens, CIF plus records, and existing MCK sanity criteria
with explicit handling of incomplete execution and ambiguity. Runtime installation
and implementation details remain open. No runtime is implemented yet.

## Task and user

A researcher supplies crystal structures and describes the intended preparation.
The application inspects each structure, selects supported operations, checks
their results, and continues until the declared batch meets the agreed checks.
The researcher can inspect changes and answer questions without writing scripts.

The first user is a wet-lab researcher supplying experimental CIF data. Prepare
starting structures by resolving disorder and adding missing hydrogens. Deliver
processed CIFs and operation/check records, not calculation-specific input decks,
an energy optimization or submitted compute jobs.

The proposed demonstration contrasts a skilled user's repeated manual work with
a conversational batch run. A 100-structure run is a demonstration target, not a
measured capability. Use real executions, authorized data and equivalent task
requirements when making a comparison.

## Shared core, two frontends

Both interfaces use the same task state, model adapter, tool interfaces,
validation policy and export path. The TUI must run in an SSH terminal without
a browser, desktop session, display server or a browser service being started.

| Part | Responsibility |
| --- | --- |
| Workflow core | Track inputs, decisions, operation outcomes and current task state |
| Model adapter | Send requests to the configured OpenAI-compatible endpoint and decode tool calls |
| Structure tools | Adapt verified MCK operations; return structured results and errors |
| Completion checker | Enforce the task policy and validate actual output artifacts |
| View adapters | Present the same structure revision through MatterVis terminal or web views |
| TUI / UI | Collect intent, show progress, accept decisions and expose outputs |

Prefer existing public interfaces over copied internals. Do not build another
agent framework or reimplement MCK chemistry to connect these pieces. The exact
task storage and frontend assembly are technical-plan decisions, not settled here.

MCK and MatterVis are checked out as pinned Git submodules under `external/`.
Keep workflow and view adapters in this repository rather than modifying the
upstream checkout to hide integration changes. See [Upstream dependencies](upstream.md)
for checkout, installation boundaries and upgrade policy.

## Execution loop

1. Register a nonempty input batch. Keep originals unchanged and assign stable
   input IDs; filenames alone are not sufficient identity.
2. Translate the request into supported operations and a proposed check policy.
  Resolve consequential ambiguity before changing structures, including disorder
  mode and output count when not supplied by the user.
3. Confirm the policy and record its check names, prerequisites and parameters.
4. Inspect each structure and collect structured findings.
5. Have the agent select an allowed operation and validated arguments. Execute
   it on a new structure revision, then re-run the required checks.
6. Continue on relevant findings. If an operation fails or produces no progress,
   use the evidence to choose a different action or request a user decision.
7. Export candidate results, reload them, and validate the exported representation.
8. Accept `finish` only when the completion checker proves the whole task is done.

Tool calls must refer to task-owned inputs/outputs and supported operations.
Model-generated shell commands, arbitrary Python execution and unrestricted file
access are not part of the initial tool interface. File content is task data,
not authority to override tool permissions or validation policy.

An individual failed strategy may be stopped based on evidence. Do not invent
an overall time, compute, model-call or experiment budget for the user.

## Meaning of completion

The user's requirement is **all structures pass sanity checks**. Implement this
as a deterministic, fail-closed condition rather than a model response:

- The input set is nonempty and every declared input has its required outputs.
  If a task produces multiple candidates, record the approved input/output mapping
  and validate every deliverable; never silently discard a difficult input.
  This means the selected delivery set, not every theoretically possible replica.
- Complete the requested disorder and hydrogen operations and resolve consequential
  warnings. An initially passing sanity report cannot substitute for an explicitly
  requested preparation step.
- The required check set is nonempty. Every required check has a result for the
  current exported structure revision and the recorded policy.
- Every required result is a real pass. Missing prerequisites, skipped execution,
  tool errors and indeterminate results remain unresolved.
- Exported files are valid and nonempty. Reload them and run the checks again;
  an in-memory report alone cannot certify a downloaded file.
- Intended changes are accounted for. Expected composition/topology constraints
  must reflect an explicitly approved operation, such as adding hydrogens, rather
  than a blanket requirement that all atom counts remain unchanged.

The agent cannot change thresholds, the required check set, expected composition,
or input membership in order to pass. A user-approved policy change is a recorded
task revision and invalidates prior completion evidence.

Pause for ambiguous scientific decisions, unavailable prerequisites or demonstrated
no-progress cycles. Paused, blocked, failed and cancelled are not successful
completion. Sanity checks establish the declared structural checks, not energetic
stability or suitability for every downstream calculation.

## Upstream integration findings

Source inspection on 2026-09-29 used MCK revision
`a271cb7eaaf333f7a1e9bfcd4ba89383de609592` and MatterVis revision
`a85cf2ab0771624afef70263069492c3a5914ecb`. These revisions are now recorded as
submodule gitlinks. The source is available locally; Python installation and
runtime integration have not been performed. Gitlinks, not this historical
inspection note, are authoritative for the current source versions.

- MCK's `molcrys_kit/analysis/sanity_check.py` exposes `sanity_check`,
  `SanityReport` and `CheckResult`. `SanityReport.passed` uses `all(results)`, so
  an empty result set passes that aggregate. Some checks also return `passed=True`
  when skipped: missing `molecule_index` for intermolecular clashes, or a missing
  or unparseable reference formula for formula consistency. Verify prerequisites
  and execution coverage explicitly; do not rely only on the aggregate boolean.
- MCK's default single-structure checks cover hard clashes, intermolecular clashes,
  isolated atoms, hydrogen presence, formula consistency and bond distances.
  Topology preservation is a separate two-structure check. These names are an API
  inventory, not a universally appropriate check policy for every material.
- The owner selected these existing MCK criteria after reviewing their limits:
  hydrogen presence means at least one H, and the current formula check compares
  element sets, not exact atom counts. Keep those meanings visible; do not claim
  complete protonation, exact stoichiometry or energetic validation from a pass.
- MatterVis web uses Dash/Plotly. `mat_viewer/app/factory.py:create_app` assembles
  a full application; it is not a standalone React component library. Prefer its
  documented scene/figure interfaces when building the new layout.
- MatterVis `TerminalViewController` and `TerminalSession` share the canonical
  terminal loader and renderer. The interactive TUI uses Textual. Controllers
  expose observation, camera, selection and focus operations; they do not supply
  a natural-language agent policy.
- Terminal observation text and view-state fingerprints are not structure
  validation. Bind observations to canonical structure revisions and use MCK
  data for scientific checks, not distances inferred from a screen projection.

References: [MCK source](https://github.com/SchrodingersCattt/MolCrysKit),
[MatterVis source](https://github.com/SchrodingersCattt/MatterVis).

## Required verification when implementation starts

Use fixtures with known problems and record expected outcomes. Test:

- Empty input/check sets, skipped checks and exceptions cannot complete a task.
- A partially passing batch cannot finish; stale reports cannot certify a changed
  structure, policy or output file.
- Export/reload failure blocks success, even after an in-memory pass.
- Repair operations preserve declared invariants; blocked cases preserve originals
  and can resume after an explicit decision.
- Both frontends show the same operation results, decisions and task status.
- TUI startup works without a display or browser dependencies. Optional web imports
  do not run just to import the core or start the TUI.
- Mocked model tests are identified as mocks. Separately verify an actual configured
  endpoint and representative end-to-end tasks before claiming live integration.

Record tool names, relevant arguments, input/output revisions, check results and
user decisions. Keep credentials out of records. Internal model reasoning is
neither required nor a substitute for executable evidence.