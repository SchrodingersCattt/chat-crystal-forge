# chat-crystal-forge

## Status

Design and dependency setup only. This repository contains engineering documents,
configuration examples and pinned upstream submodules. The application and the
planned `mat-chat tui` / `mat-chat ui` commands are not implemented yet.

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
does not include initialized submodules. Python installation instructions will be
added when the runtime is implemented and verified.

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
in local `.env` or the process environment; never commit them. The model adapter
and configuration loader are not implemented yet.

## License

Original material in this repository is available under the [MIT license](LICENSE).
Upstream code, data and assets retain their own terms. See [Licensing](docs/licensing.md).