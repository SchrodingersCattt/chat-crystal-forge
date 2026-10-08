# chat-crystal-forge

## Status

The current implementation provides a shared inspection and preparation workflow.
Forge Chat panels run inside the actual MatterVis Web UI and TUI; SQLite records
revisions, decisions, isolated jobs and independently reloaded exports. Completion
is code-gated and never inferred from model prose.

Natural-language tool calling is implemented but needs your configured endpoint
and model. Direct inspection commands work without an API key. Unit tests using
mocked model responses do not establish live-provider compatibility.

## Install and try the development preview

Use Python 3.11+ in an activated virtual environment and initialize submodules.
Install the source checkouts and app with
`python -m pip install -e external/molcryskit -e "external/mattervis[all,test]" -e ".[dev]"`.
The MatterVis checkout must include the optional frontend extension interface;
an older PyPI release alone does not provide it.

- `mat-chat ui` starts a loopback-only Web app at `http://127.0.0.1:8050`.
- `mat-chat tui` starts the native terminal viewer with the chat panel.
- `mat-chat serve` starts CrystalForge's standalone session API at port 8051;
  it owns its own SQLite session directories and does not depend on the
  separate `mattervis-saas` repository.
- Supply CIF paths after either subcommand to inspect your own inputs.
- Without paths, a bundled **synthetic water geometry**, not experimental data,
  is registered and shown.
- `/inspect` runs MCK checks on all registered copies; `/inspect <id>` selects one.
- `/complete-h <id> [formula]` performs isolated hydrogen completion after an
  explicit formula decision when the input is ambiguous.
- `/disorder <id> <optimal|random|enumerate> <count> [seed] [coupled]` generates
  a bounded delivery and records requested, returned, distinct and duplicate counts.
- `/export <id> [formula]` writes a CIF, reloads it and runs all six checks; `/finish`
  is allowed only when every declared input has a passing non-stale export and that
  file no longer contains disorder.
- `/list` shows registered IDs, `/load <path>` registers another CIF, `/help` lists
  direct commands. Natural-language messages use the configured model.
- `--session <directory>` restores a saved session; new launches otherwise create
  separate directories under `.crystalforge/`. This directory is ignored by Git.

Inspection and preparation target immutable registered copies. Native viewer
camera/selection state is presentation-only; a changed registered revision or
policy invalidates earlier export evidence and requires a new `/load`.

Run `python -B -m pytest tests` and `ruff check src tests` for the parent package.
Run upstream tests from `external/mattervis`, not the parent working directory.
See [the runnable demo](examples/DEMO.md), [Implementation plan](docs/implementation-plan.md)
and [Build checklist](devpost/checklist.md) for validation details.

## Planned task

An owner-supplied experimental input is tracked at
[`examples/structures/DAP-4.cif`](examples/structures/DAP-4.cif).
See [example provenance and usage](examples/README.md). It is separate from the
bundled synthetic water demo and the upstream historical oracle fixture.

Prepare experimental molecular-crystal CIFs with disorder and missing hydrogens.
The terminal and browser interfaces will share an agentic preparation workflow,
use explicit user decisions for ambiguous cases, and deliver processed CIF files
with operation and MCK sanity-check records.

The first release targets structural preparation, not generation or execution of
calculation-specific input decks. See [Structure preparation](docs/structure-preparation.md)
for the agreed task, native MCK check meanings and completion conditions.

## Source checkout

Initialize the recorded dependencies with `git submodule update --init --recursive`
after cloning, or clone with `--recurse-submodules`. A parent-repository ZIP alone
does not include initialized submodules.

- [MolCrysKit](https://github.com/SchrodingersCattt/MolCrysKit), under
  `external/molcryskit`, provides reused structure-perception/operation capabilities.
- [MatterVis](https://github.com/SchrodingersCattt/MatterVis), under
  `external/mattervis`, provides reused terminal and web visualization capabilities.

These are pre-existing projects, not new engines implemented here. Their pins,
update procedure and attribution are described in [Upstream dependencies](docs/upstream.md).

## Development references

- [AGENTS.md](AGENTS.md): development guidance and documentation index.
- [Architecture](docs/architecture.md): workflow and integration boundaries.
- [Interfaces](docs/interfaces.md): planned CLI, TUI and browser layout.
- [Configuration](docs/configuration.md): proposed OpenAI-compatible settings.
- [Decisions](docs/decisions.md): confirmed scope and outstanding implementation work.

`.env.example` has empty credential/model placeholders. Keep actual credentials
in local `.env` or the process environment; never commit them. Environment settings
override the launch directory's `.env`, or the explicit `--env-file` supplied.

## License

Original material in this repository is available under the [MIT license](LICENSE).
Upstream code, data and assets retain their own terms. See [Licensing](docs/licensing.md).
