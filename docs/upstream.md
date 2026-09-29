# Upstream dependencies

MCK and MatterVis are pre-existing projects by the repository owner. This project
reuses them openly as Git submodules, preserving their source repositories and
history. It adds the conversational preparation workflow and its integration;
it does not claim to have newly implemented the upstream engines.

## Sources and responsibilities

| Submodule path | Source | Reused capability |
| --- | --- | --- |
| `external/molcryskit` | [MolCrysKit](https://github.com/SchrodingersCattt/MolCrysKit) | Structure perception, selected structure operations and sanity-check functions |
| `external/mattervis` | [MatterVis](https://github.com/SchrodingersCattt/MatterVis) | Terminal controllers/rendering, web scene/figure construction and suitable UI capabilities |

The initial source pins on 2026-09-29 are MCK
`a271cb7eaaf333f7a1e9bfcd4ba89383de609592` and MatterVis
`a85cf2ab0771624afef70263069492c3a5914ecb`. The Git tree's submodule entries are
the version lock; this paragraph records the initial checkout rather than another
lock file to keep synchronized.

New work belongs in the parent repository: model/tool adapters, batch task state,
the inspect–repair–validate loop, strict completion checks, shared TUI/UI workflow,
and tests and examples for the declared task. Keep view and workflow adapters here
unless an upstream change is specifically requested and reviewed.

## Checkout and reproducibility

[`.gitmodules`](../.gitmodules) records the public HTTPS URLs, paths and `main`
branches. Each `160000` Git entry records one exact upstream commit. The branch
setting selects the source for an explicit remote update; ordinary checkout does
not automatically follow the latest `main`.

- Clone the parent repository with `--recurse-submodules`, or run
  `git submodule update --init --recursive` after cloning it normally.
- Use `git submodule status` to inspect the checked-out revisions. An uninitialized
  or mismatched submodule must not be silently replaced by an unrelated package.
- CI and reproducibility checks must initialize the recorded revisions rather
  than use `git submodule update --remote` during routine setup.
- A downloaded ZIP of the parent repository alone does not provide initialized
  submodule contents. Document this when packaging or distributing source.

The checkout procedure has been verified locally. Neither package has been
installed into a project Python environment yet. Source tracking is not runtime
integration, and no application startup commands are available yet.

## Runtime installation boundary

When the technical plan establishes a Python environment, make development and
CI use these recorded source revisions. Verify that imports resolve to the
intended checkouts rather than older or unrelated PyPI installations.

MatterVis itself depends on `molcrys-kit`; ensure it uses the same MCK checkout
as the workflow. Pinning two sources does not prove their runtime compatibility.
Select optional dependencies for the chosen interfaces, keeping web startup and
imports out of terminal-only execution. Package release metadata and installation
commands still need to be implemented and tested; submodules alone are not a
PyPI dependency solution.

## Upgrading a dependency

1. Confirm that the upgrade is part of the current task. Check the parent and both
   submodule worktrees; preserve existing edits and local commits.
2. Inspect the upstream change and choose a commit. Update only the intended
   submodule; do not reset or discard its worktree to force an update.
3. Reinstall/rebuild the affected dependency in the project environment as needed.
   Verify required APIs and run the integration tests, including both frontend
   paths and validation failure cases.
4. Stage the changed submodule gitlink in the parent repository and commit it with
   any required adapter/test updates. Explain the upgrade and verification.
5. If an authorized change was made inside a submodule, it needs its own upstream
   commit and a reachable remote reference before the parent pin can be shared.
   Never publish a parent pin that only exists on a local machine.

Do not treat a parent commit as a commit of uncommitted files inside a submodule.
Do not suppress dirty-submodule reporting or enable automatic source upgrades.

## Attribution and licenses

The parent MIT license covers its original material. Preserve each upstream's
license and copyright notices, including when adapting individual components.
Document copied or modified code if a later integration requires it. Check data
and asset permissions separately before using upstream examples in a public demo.

MCK includes an MIT license file. At the initial pin, MatterVis declares MIT in
its README and package metadata but has no license-text file in its source tree;
the required notice should be confirmed before redistribution of adapted code.
No upstream code or license file was changed by this integration.
See [Licensing](licensing.md) for the owner's commercial-use choice and details.