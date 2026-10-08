# CrystalForge DAP-4 demo

This walkthrough uses the native MatterVis host and CrystalForge's local
session state. It does not install or call `mattervis-saas`.

## Browser path

Install the pinned editable sources, then start the UI:

```bash
python -m pip install -e external/molcryskit -e "external/mattervis[all,test]" -e ".[dev]"
mat-chat ui examples/structures/DAP-4.cif --session .crystalforge/dap4-demo
```

In the Chat panel run:

```text
/inspect
/complete-h <id>
```

The input has an ambiguous `?` moiety, so the second command must stop and ask
for a reference. Confirm `C6 H18 Cl3 N3 O12`, then choose a bounded disorder
delivery and complete the workflow:

```text
/complete-h <id> C6 H18 Cl3 N3 O12
/disorder <id> optimal 1
/export <id> C6 H18 Cl3 N3 O12
/finish
```

The original file in `examples/structures/` is never modified. The Chat panel
shows the reload report, including all six checks and the export path.

## Rejection and recovery paths

Before exporting, `/finish` returns `missing_export`. Exporting the
hydrogenated crystal while disorder remains returns `disorder_unresolved`.
`/finish` passes only after that export no longer has disorder and the six
reloaded checks pass. A malformed export or a changed revision returns a
blocked result and leaves the evidence in SQLite.
Stop the process during a preparation job, then reopen the same directory:

```bash
mat-chat ui --session .crystalforge/dap4-demo
mat-chat tui --session .crystalforge/dap4-demo
```

The job remains `interrupted` until a new explicit command is submitted; it is
never silently replayed.

## Terminal and HTTP checks

The terminal host reads the same session snapshot without starting a browser:

```bash
mat-chat tui --session .crystalforge/dap4-demo
```

The optional standalone API is independent of MatterVis SaaS:

```bash
mat-chat serve --root .crystalforge --port 8051
curl http://127.0.0.1:8051/healthz
curl -X POST http://127.0.0.1:8051/v1/sessions
```

Natural-language requests require local `OPENAI_API_KEY`, `OPENAI_BASE_URL` and
`OPENAI_MODEL`. Direct slash commands work without those settings, and secrets
never enter the browser payload or session database.
