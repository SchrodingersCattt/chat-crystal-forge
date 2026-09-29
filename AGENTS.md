# Project Guidelines

## Purpose and current state

`chat-crystal-forge` (working product name: CrystalForge) is a conversational
workspace for preparing molecular-crystal structures. Its core is an agentic
inspect–repair–validate loop, shared by a terminal interface and a browser UI.
The first task is experimental CIF preparation for wet-lab users: disorder
resolution and hydrogen completion, ending in CIF files and operation/check records.
Reuse MolCrysKit for structure perception and approved operations, and MatterVis
for visualization. Build the workflow and real task experience, not a new
chemistry engine or a generic chatbot.

The first implementation is a read-only inspection preview: native MatterVis
UI/TUI plus Forge Chat, registered CIF copies, MCK reports and persisted sessions.
Repairs, full batch recovery and `finish` are not implemented. Distinguish live
endpoint verification from mocked protocol tests and direct inspection commands.

## Read before changing an area

| Area | Reference |
| --- | --- |
| Workflow, adapters, completion checks, testing | [Architecture](docs/architecture.md) |
| Implementation sequence and current delivery status | [Implementation plan](docs/implementation-plan.md) |
| Native UI/TUI extension contract | [Plugin protocol](docs/plugin-protocol.md) |
| Disorder, missing hydrogens and MCK acceptance | [Structure preparation](docs/structure-preparation.md) |
| CLI, TUI, browser panels, typography and colors | [Interfaces](docs/interfaces.md) |
| OpenAI-compatible endpoints and environment variables | [Configuration](docs/configuration.md) |
| Submodule checkout, upgrades and reuse boundaries | [Upstream dependencies](docs/upstream.md) |
| Commercial use and upstream code reuse | [Licensing](docs/licensing.md) |
| Confirmed requirements and decisions awaiting the owner | [Decisions](docs/decisions.md) |

Keep this file short. Update the relevant document when a design changes; do not
duplicate detailed specifications here. Keep product behavior, branding and
development instructions independent of the context in which the project is shown.

## Integrity and implementation guidance

The first repair scope, MCK acceptance policy and two frontends are confirmed.
The mechanisms below are working design guidance; remaining implementation details
and task-specific scientific choices are recorded in the decision log.

- Keep one workflow core for TUI and UI. Frontends present state and user decisions;
	they must not implement separate repair or validation policies.
- Let the model propose actions; execute them through validated tool interfaces.
	Never accept model-written claims as evidence that a tool ran or a check passed.
- Gate `finish` in code: a nonempty batch, every declared input accounted for,
	all required checks actually executed and passed, and exported artifacts
	independently reloaded and validated under the same policy.
- A skipped check, missing result, missing output, or exception is not a pass.
	Do not weaken checks or remove failed inputs to manufacture completion.
- Use the existing MCK sanity criteria for the first release, not a new chemistry
	validation engine. Ask for unresolved disorder strategy/count and chemical
	ambiguity; do not silently enumerate every replica or equate `optimal` with energy.
- Preserve original inputs and operation history. Ask for scientific decisions
	when evidence is insufficient; detect repeated no-progress attempts and expose
	the unresolved state rather than retrying indefinitely.
- Use stable structure/atom identities when connecting observations to views.
	Camera, selection and display changes must not modify scientific data.
- Keep API keys local to the process making model requests. Never commit `.env`,
	expose keys to the browser, or include secrets in logs, screenshots or examples.
- Verify installed upstream APIs before integrating them. Preserve required
	notices; do not silently copy or modify unrelated upstream repositories.
- Treat `external/molcryskit` and `external/mattervis` as pinned Git submodules.
	Generic plugin hooks/viewer bugs belong in MatterVis; chemistry bugs belong in
	MCK; workflow bugs belong here. Task-related upstream fixes are authorized:
	reproduce, add regressions, validate, then push/PR upstream before advancing
	parent pins. Never mask upstream races with sleeps or duplicate view state.

## Development practice

Read the affected code and existing tests before editing. Implement the smallest
verified step; discuss unresolved product choices instead of silently choosing
them. Use kebab-case for repository/distribution names, snake_case for Python
modules and functions, PascalCase for classes, and camelCase for JavaScript.

Install editable MCK and MatterVis submodules before the parent package; see the
README for exact commands. Run `python -B -m pytest tests` and `ruff check src tests`
in the parent. Run the full MatterVis suite from its own directory. Keep optional
browser dependencies out of TUI startup. Test blocked states as well as success.
For Python syntax-only checks, prefer AST parsing over generating bytecode files.

Keep task files in this workspace. Use `gh`/HTTP APIs for repository research,
not browser automation; browser tools may be used to validate the local UI.
Before committing, inspect the diff and staged paths and include only this task's
files. Do not create or publish a remote repository without authorization.
