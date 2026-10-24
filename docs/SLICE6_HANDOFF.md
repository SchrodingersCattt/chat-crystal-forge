# Slice 6 handoff — user hands-on (DAP-4)

Status: **Slices 1–5 done in code.** Slice 6 is install reproducibility, demo/docs
final polish, and **user** hands-on + Final Review. This note lists the exact
commands from [`examples/DEMO.md`](../examples/DEMO.md) and what “pass” looks like.
Mechanical install/test notes live in [`docs/validation.md`](validation.md) and
[`devpost/checklist.md`](../devpost/checklist.md).

## Prerequisites (once)

From a clean checkout with Python 3.11+ and an activated venv:

```bash
git submodule update --init
python -m pip install -e external/molcryskit -e "external/mattervis[all,test]" -e ".[dev]"
```

Optional for natural-language chat only: local `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
`OPENAI_MODEL`. Slash commands below work without them.

## DAP-4 happy path (inspect → complete-h → disorder → export → finish)

Start the browser host on the authorized demo input (does not modify
`examples/structures/DAP-4.cif`):

```bash
mat-chat ui examples/structures/DAP-4.cif --session .crystalforge/dap4-demo
```

In the Chat panel, run in order:

```text
/inspect
/complete-h <id>
```

DAP-4 has an ambiguous `?` moiety, so `/complete-h <id>` must **stop and ask**
for a reference. Confirm the formula, then continue:

```text
/complete-h <id> C6 H18 Cl3 N3 O12
/disorder <id> optimal 1
/export <id> C6 H18 Cl3 N3 O12
/finish
```

Replace `<id>` with the structure id shown by `/list` or the inspect result.

Terminal host on the same session (no browser):

```bash
mat-chat tui --session .crystalforge/dap4-demo
```

## What “pass” looks like

| Step | Pass signal |
| --- | --- |
| `/inspect` | Six MCK checks reported on the registered copy; original file under `examples/structures/` unchanged. |
| `/complete-h <id>` (no formula) | Stops with an ambiguity / formula question (`awaiting_decision`), not a silent repair. |
| `/complete-h <id> C6 H18 Cl3 N3 O12` | Isolated hydrogen completion produces a candidate revision with records. |
| `/disorder <id> optimal 1` | Bounded delivery with requested/returned/distinct counts; choice and provenance recorded. |
| `/export <id> …` | Writes a CIF, **reloads** it, runs all six checks; Chat shows the reload report and export path. |
| `/finish` | Succeeds only when every declared input has a **non-stale** passing export **and** that file no longer contains disorder. |

## Rejection paths (also part of pass criteria)

| Situation | Expected result |
| --- | --- |
| `/finish` before any export | `missing_export` (or equivalent blocked finish). |
| Export while disorder remains | `disorder_unresolved` (or equivalent blocked export). |
| Malformed export / changed revision | Blocked result; evidence stays in SQLite (not silently “all pass”). |
| Kill the process mid-job, reopen `--session .crystalforge/dap4-demo` | Job stays `interrupted` until a **new explicit** command; never auto-replayed. |

## Code polish already on main (agent)

Forge-only Chat presentation is on `main` (Tool Execution cards, revision strip,
humanized blocked-finish copy, DEMO rejection wording). Submodules pinned MatterVis
`v0.0.6` / MolCrysKit `v0.8.0`. Remaining Slice 6 items below are **user-only**.

## Slice 6 remaining — user-only

These stay open until Ming-Yu explicitly confirms (do not mark from agent runs alone):

1. Follow install + DAP-4 path above (UI and/or TUI); note clarity issues.
2. Try at least one rejection/recovery path from the table.
3. Checklist boxes still open: Final kick-the-tires, Final Review, live Code Tour /
   learner wrap-up confirmation (`devpost/app-map.html` static route already exists).
4. Say ready / not ready to ship; agent then updates checklist Slice 6 and Final Review.

Do not commit junk paths (`agent/`, `_tmp/`, `pelican-bike.html`, local `.crystalforge/` sessions).
