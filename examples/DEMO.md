# CrystalForge DAP-4 demo

This walkthrough uses the native MatterVis host and CrystalForge's local
session state. It does not install or call `mattervis-saas`.

Chat tools edit **registered copies** only. After an Operation, reload the
structure in the center viewer manually until MatterVis ships an extension
write API ([MatterVis#217](https://github.com/SchrodingersCattt/MatterVis/issues/217)).
Scene tabs are presentation slots, not scientific versions
([MatterVis#218](https://github.com/SchrodingersCattt/MatterVis/issues/218),
[MatterVis#219](https://github.com/SchrodingersCattt/MatterVis/issues/219)).

## Install once

```bash
python -m pip install -e external/molcryskit -e "external/mattervis[all,test]" -e ".[dev]"
```

## DAP-4 happy path (browser)

Start the UI on the authorized demo input (does not modify
`examples/structures/DAP-4.cif`):

```bash
mat-chat ui examples/structures/DAP-4.cif --session .crystalforge/dap4-demo
```

In the Chat panel, Tool Execution cards show tool name, key args, status and a
short result. The Chat header has a text-size control: **S**, **M** (default),
**L** and **XL**. The choice is saved in this browser and restored the next time
you open `mat-chat ui`. It changes type in the Chat panel (messages, tool cards,
captions and the composer) and does not change the 3D viewer. At XL, cards and
slash commands wrap inside the panel.

Run in order:

```text
/inspect
/list
/complete-h <id>
```

DAP-4 has an ambiguous `?` moiety, so `/complete-h <id>` **must stop and ask**
for a reference (`awaiting_decision`). Confirm the formula, then finish:

```text
/complete-h <id> C6 H18 Cl3 N3 O12
/disorder <id> optimal 1
/export <id> C6 H18 Cl3 N3 O12
/finish
```

Replace `<id>` with the structure id from `/list` or the inspect card. The Chat
revision strip lists scientific copies from the session snapshot; reload the
center Scene yourself after preparation steps if the viewer still shows the
launch-time file.

Pass signals: six MCK checks on the registered copy; hydrogen completion and
bounded disorder each create a revision; export reloads all six checks; `/finish`
succeeds only with a non-stale passing export that no longer contains disorder.

## Rejection paths (try at least one)

**Before any export**, run:

```text
/finish
```

Expected Tool Execution card: status **Blocked**, short result like
`Finish blocked: … no certified export yet — run /export first` (`missing_export`).
Evidence stays in the session; `/finish` does not invent a pass.

**Optional second check** — after `/complete-h` but before disorder is resolved,
exporting or finishing should show `disorder_unresolved` (or a blocked export).
Interrupted mid-job recovery is covered in
[`docs/SLICE6_HANDOFF.md`](../docs/SLICE6_HANDOFF.md).

## Terminal and HTTP checks

Same session without a browser:

```bash
mat-chat tui --session .crystalforge/dap4-demo
```

Optional standalone API (independent of MatterVis SaaS):

```bash
mat-chat serve --root .crystalforge --port 8051
curl http://127.0.0.1:8051/healthz
curl -X POST http://127.0.0.1:8051/v1/sessions
```

Natural-language requests need local `OPENAI_API_KEY`, `OPENAI_BASE_URL` and
`OPENAI_MODEL`. Slash commands work without them; secrets never enter the
browser payload or session database. Install evidence:
[`docs/validation.md`](../docs/validation.md).
