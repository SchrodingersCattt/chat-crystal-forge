# Design decisions

This is an engineering decision log, not an approved implementation specification.
Record explicit user choices separately from recommendations. A draft document
does not establish that its proposed behavior has been implemented or approved.

## Confirmed requirements

- Continue the current molecular-crystal preparation idea.
- First users are wet-lab researchers with experimental CIFs; first repairs are
  disorder resolution and missing-hydrogen completion.
- First-release outputs are processed CIFs and operation/check records, without
  calculation-specific input files or compute submission.
- The distinctive work is the agentic workflow and a real problem demonstration.
- MCK structure perception and MatterVis UI/TUI capabilities may be reused.
- Successful completion requires all structures to pass sanity checks.
- Support terminal and browser interfaces for workstation and SSH-server use.
- Ship the same core journey in both first-release interfaces: chat, processing,
  check-result review, exception decisions and export. Rendering details may differ.
- Put the structure workspace on the left and conversation on the right.
- Use predominantly white/light-gray surfaces, with dark gray, dark blue, dark
  teal and crimson accents. Use Arial and Consolas where the frontend can control
  fonts; terminal fonts remain terminal-controlled.
- Use a tracked `.env.example`, an ignored `.env`, and OpenAI-compatible API-key,
  base-URL and model-SKU configuration.
- Keep detailed documentation under `docs/` and link it from root `AGENTS.md`.

## Confirmed decisions (2026-09-29)

### D1. License and commercial intent

**Confirmed: MIT.** The user selected MIT after discussing permissive commercial
use and the Apache-2.0 alternative. This allows proprietary commercial reuse by
the owner and by others. See [Licensing](licensing.md) and the root [LICENSE](../LICENSE).

### D2. CLI spelling

**Confirmed: `mat-chat tui` / `mat-chat ui`.** The user chose the symmetric pair
instead of `start-ui`. No additional alias is planned. Names in
[Interfaces](interfaces.md) are not published package identifiers yet.

### D3. First scientific task and check policy

**Confirmed: disorder and missing hydrogens; use current MCK sanity criteria.**
The user selected this policy after the existing hydrogen-presence and
element-set-only formula checks were explained. Do not introduce an independent
chemistry validation engine or change upstream checks for the first release.

Ask for unresolved disorder delivery strategy (`optimal`, `random`, `enumerate`),
requested candidate count and other scientific ambiguity. Never generate every
replica merely because a scan found many possibilities. Apply explicit user choices
without repeatedly asking, and handle warnings, incomplete coverage and missing
results separately from MCK's booleans. See [Structure preparation](structure-preparation.md).

### D4. First-release TUI/UI parity

**Confirmed: both frontends complete the same core workflow in the first release.**
They support chat, processing, check results, exception decisions and export;
rendering details may differ. Do not reduce the TUI to a log viewer or defer one
frontend beyond the first release without revisiting this decision with the user.
The development sequence inside that release is not prescribed.

### D5. Upstream source tracking and attribution

**Confirmed: use Git submodules and openly identify reused work.** MCK is checked
out at `external/molcryskit`, and MatterVis at `external/mattervis`, from the user's
existing public upstream repositories. The parent repository records commit pins;
upgrades are explicit. The new work is the agentic workflow, shared task state,
integration and real task demonstration, not the existing structure or rendering
engines. See [Upstream dependencies](upstream.md).

### D6. GitHub publication

**Confirmed: public repository and push authorized.** The user authorized creation
of `SchrodingersCattt/chat-crystal-forge` through the authenticated GitHub account,
and explicitly selected public visibility after being informed that source and
Git history will be readable. Review files/history for secrets before publishing;
exclude `.env`, personal profiles and unrelated local tooling directories.

## Still needed for implementation and evaluation

- A representative input set and permission to redistribute any public demo data.
  A proposed 100-input demonstration is not a completed benchmark.
- Actual endpoint/model configuration, supplied locally rather than in chat.
- The technical implementation plan and runtime integration tests.

Disorder strategy and chemically ambiguous choices are task-specific runtime
decisions, not a reason to hard-code one universal mode during project setup.

## Proposed implementation safeguards

These support the requested all-pass condition and are spelled out in
[Architecture](architecture.md): preserved originals, explicit scientific decisions,
fixed validation policy per task revision, check-coverage verification, exported-file
revalidation and evidence-based no-progress handling. They are draft implementation
requirements, not evidence that checks have already run.

## Current status

Instructions, design drafts, configuration examples and pinned upstream source
have been prepared. A local Git repository has been initialized and public GitHub
publication has been authorized.
No application entry point, repair workflow, live model integration or published
package exists in this workspace yet. These documents do not complete any separate
planning/review process automatically.