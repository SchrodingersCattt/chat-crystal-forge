# Experimental CIF preparation

Status: the owner confirmed the first task, deliverables and acceptance scope on
2026-09-29. The integration below is a design contract, not an implemented or
runtime-tested workflow. Source observations refer to the initial pinned MCK
revision `a271cb7`.

## First task

A wet-lab researcher supplies experimental molecular-crystal CIFs with disorder,
missing hydrogens, or both. The application prepares starting structures for
subsequent computational modeling. It delivers processed CIF files and records
of operations, decisions, warnings and MCK checks.

The first release does not generate calculation-specific input decks, choose
electronic-structure settings, optimize energies or submit jobs. Both TUI and UI
must support the same preparation, decision and export workflow.

## Automatic work and user decisions

Automatically inspect inputs, identify the applicable operations, execute already
authorized choices, run MCK checks and prepare verified exports. Preserve originals.
Ask only when the request or a saved task policy leaves a consequential choice open.

| Situation | Required behavior |
| --- | --- |
| Disorder without a specified delivery strategy | Ask which MCK mode and how many outputs are wanted before generation |
| Many possible disorder choices | Offer a bounded delivery choice; do not enumerate everything to discover an exact total |
| Explicit mode/count already supplied | Apply it without asking again for each compatible structure |
| Random sampling | Record the seed and explain MCK's native reference-replica behavior |
| Ambiguous coupling of symmetry-related disorder choices | Explain independent versus coupled choices and obtain a decision if it affects the intended task |
| Unambiguous hydrogen completion within the requested task | Call MCK and check the resulting structure; retain relevant warnings |
| Ambiguous moiety assignment, protonation, charge or proton site | Present the available evidence and ask; geometry alone does not establish the experimental assignment |
| Missing/conflicting formula reference | Ask for or confirm a reference independent of the generated output |
| H placement shortfall, excess H, unsatisfied correction or solver fallback | Diagnose and resolve, or pause for a decision; a returned object is not proof of completion |
| Fewer or duplicate candidates relative to the delivery request | Report requested, returned and distinct-selection counts separately; do not count duplicates as independent requested samples |
| Multiple CIF data blocks | Ask which data should be processed rather than silently accepting only the first block |
| Failed checks or repeated no-progress attempts | Preserve the latest evidence and show a blocked state; do not relax checks to obtain success |

Ask once for a batch policy when its assumptions apply throughout the batch.
New evidence that invalidates those assumptions may require another question.
An accepted warning is a recorded scientific decision, not a mechanism to waive
failed mandatory checks. Informational and consequential warnings should be
distinguished rather than treating every log line as an error or hiding all warnings.

## Disorder contract

Inspect with `scan_cif_disorder` and load with `resolve_disorder=False`.
The convenience reader option `resolve_disorder=True` selects an `optimal` replica
and must not bypass the user's choice.

Use the public `generate_ordered_replicas_from_disordered_sites` interface.
Relevant parameters are `filepath` or `crystal` (exactly one), `generate_count`,
`method`, `random_seed`, `return_kept_indices` and `coupled`.

| MCK mode | Meaning at the pinned revision |
| --- | --- |
| `optimal` | One greedy occupancy/conflict-graph selection; not an energy minimum or a proof of a global optimum |
| `random` | Occupancy-weighted sampling that starts from a deterministic reference replica; seed and requested count must be recorded |
| `enumerate` | Deterministic combinations of internally retained alternatives, with a positive requested count acting as a cap; not guaranteed exhaustive enumeration |

Do not present `random` with one returned reference replica as proof of independent
random sampling. Postprocessing can produce duplicate retained selections in
random/enumeration modes. Report what MCK actually returned. Distinct source-index
selections are not proof of crystallographically inequivalent structures.

There is no public cheap API for the exact number of distinct valid candidates.
MCK bounds some intermediate alternatives, and its return value does not include
a reliable exhaustive/truncated-total flag. Display known scan facts and label
unknown candidate totals honestly. Do not introduce an invented project-wide
resource budget; the task's chosen output count controls the requested delivery.

Prefer the original filepath generation path for experimental CIFs. At this pin,
the in-memory conversion does not preserve all moiety/Z fields used by the solver.
Keep the original scan metadata and source-index provenance in task-owned records.

## Hydrogen completion contract

`add_hydrogens` returns a new `MolecularCrystal`, not a completion certificate.
It supports target elements, geometric rules and bond lengths, optional torsion
handling and `use_formula_moiety`. Placement uses MCK's chemistry/geometry heuristics.
The API does not accept a general protonation-state or total-charge specification.

Retain an agreed `formula_moiety` from the input or user decision and explicitly
carry it onto adapter-owned replicas before completion when applicable. Keep
provenance outside the structure object: intermediate operations do not preserve
all source metadata automatically.

Handle partially hydrogenated inputs as well as H-free inputs. A single existing
H atom must not cause a requested hydrogen-completion step to be skipped. A parsed
but unmatched or ambiguous moiety can suppress additions; placement shortfalls
may warn or raise. Surface these outcomes rather than equating a successful return
with complete hydrogen assignment.

## MCK acceptance policy

Use `sanity_check` with the existing default six checks and recorded MCK settings.
The owner chose these criteria after reviewing their current limits. Preserve the
native result and display its actual meaning rather than replacing it with new
chemistry thresholds.

| Check | What the current implementation checks |
| --- | --- |
| `hard_clash` | Short atom-pair distances using a radius-based threshold; default scale 0.6 and tolerance 0 |
| `intermolecular_clash` | Short intermolecular/periodic-image contacts; default scale 0.8, tolerance 0, no ignored H–H pairs and zero allowed clashes |
| `isolated_atoms` | Single-atom molecules for the configured suspect elements, not every possible undercoordinated site |
| `hydrogen_presence` | At least one hydrogen atom is present, not site-by-site hydrogen completeness |
| `formula_consistency` | Element-set agreement with a reference, not exact atom-count or molecular-multiplicity agreement |
| `bond_distances` | Lengths of perceived candidate bonds relative to radii; not a guarantee that all intended bonds were found |

Read effective defaults from MCK instead of maintaining a divergent local copy.
Its standalone topology-preservation function is not part of the default six.
The default six also contain no explicit disorder-resolution check. Therefore,
check results do not replace evidence that the requested preparation steps ran.

MCK can return `passed=True` for a skipped check and for an empty report. The adapter
must require the expected result set, prerequisites and task coverage. Supply a
frozen, independently accepted `reference_formula` explicitly rather than deriving
it from the output under test. Missing or unparseable references remain unresolved;
do not label them as a completed formula check.

No extra chemistry validation engine is requested. The adapter's completeness,
provenance and exception handling make execution truthful without claiming that
MCK verifies complete protonation, exact stoichiometry or energetic stability.

## Export and finish

Export each agreed output with MCK, then load the actual exported CIF without
automatic disorder resolution and run the same MCK policy and external reference.
Preserve cell/formula references and operation provenance in accompanying records:
the CIF writer does not serialize all task metadata or the full preparation history.

The delivery record should identify the input, selected strategy, requested and
actual output counts, random seed where relevant, coupling, significant warnings,
user decisions and pre-/post-export reports. JSON is the proposed machine-readable
record format; the UI should also make the results readable without opening JSON.

`finish` requires every input's **agreed delivery set** to exist, the requested
operations and consequential ambiguities to be handled, and every delivered
structure to pass the executed MCK checks after reload. It does not mean generating
all theoretically possible replicas. Unresolved cases stay visible and prevent
the batch from being presented as wholly completed.

## Source references and verification

The contracts above were inspected in the pinned source, not executed:

- `molcrys_kit/io/cif.py`: `scan_cif_disorder`, `read_mol_crystal`, `DisorderInfo`.
- `molcrys_kit/analysis/disorder/process.py` and `solver.py`: modes and generation.
- `molcrys_kit/operations/hydrogen_completion.py`: addition behavior and warnings.
- `molcrys_kit/analysis/sanity_check.py` and `constants/config.py`: criteria/defaults.
- `molcrys_kit/io/output.py`: CIF export and serialized metadata.

Integration tests must cover H-free and partial-H inputs, explicit disorder
strategies, replica shortages/duplicates, skipped checks, metadata preservation,
ambiguous chemistry and export/reload. Inspecting upstream tests is not a substitute
for running this application's integration tests once implemented.