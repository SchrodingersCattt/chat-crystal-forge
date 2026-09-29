# MatterVis / Forge plugin protocol

## Contract status and boundary

The following is the minimal first-slice extension contract being integrated by
main. The generic upstream host patch is under validation, not published; this
document does not certify compatibility or a bug fix. The richer versioned
command/event protocol below is future design, not an existing API.

MatterVis hosts optional extensions in its **actual** Dash and Textual apps.
Forge supplies chat and task policy without replacing the native viewer. No Forge
import is required for ordinary MatterVis startup.

## Minimal first-slice surface

`mat_viewer.extensions.Extension` takes a namespaced `name` and exposes:

| Hook | Responsibility |
| --- | --- |
| `build_web_panel(context)` | Construct the extension's web panel |
| `register_web(app, context)` | Register its web callbacks during app construction |
| `build_tui_panel(context)` | Construct the extension's terminal panel |
| `on_tui_mount(app, context)` | Attach terminal-side activity when mounted |
| `on_tui_unmount(app, context)` | Stop terminal-side activity when unmounted |
| `close()` | Release extension-owned resources |

Web construction is `create_app(..., *, extensions=())`; terminal construction is
`CrystalTUI(crystal, *, ..., extensions=())`. Empty extensions preserve native use.
These are integration signatures, not a promise that every upstream release has
them. Verify the installed pin before calling them.

Context `viewer` is the **same** native backend/app, not a parallel controller.
Context snapshots are detached observations, not writable handles into native
state. Namespaced component IDs prevent host/extension collisions. Web callbacks
are registered at construction; this contract does not provide hot callback
unregistration or dynamic lifecycle replacement. Cleanup must respect that limit.
Precise context fields and hook return types remain subject to main's validation;
do not invent additional callable methods from this table.

## Forge service boundary

Initial service: `ForgeService(workspace, settings=None, client=None)`.
`add_input(Path)` registers an input; `submit(text)` returns a turn ID;
`snapshot()` returns a detached dictionary with `messages`, `structures`, `busy`,
`error`, `status`; `close()` cleans up service resources. Frontends render this
state and route intent to this service rather than deciding check outcomes.

One background thread performs first-slice read-only work. Publish state safely
and do not share mutable MCK structures with native rendering callbacks. Verify
close/unmount during work and late-result handling. Do not claim cancellation can
forcibly terminate an in-flight Python thread. Process jobs and durable recovery
come later.

`/load`, `/list`, `/inspect`, `/help` are direct local commands, visibly distinct
from AI execution. Natural-language turns use the configured endpoint. No mutation
or `finish` tool is exposed in this slice.

## Identity and invalidation

MatterVis owns camera, display, selection, native operation state and rendering
concurrency. Forge owns input lineage, scientific revisions, decisions and check
evidence. Stable source atom IDs must map explicitly to displayed copies; a
periodic/symmetry copy is not another independent source atom. A detached snapshot
does not itself establish scientific revision identity.

Before enabling repairs, manual native scientific edits must create an explicit
revision/invalidation boundary. Reject stale inspection/check/job results after
such edits. Pure camera, focus and display changes must not invalidate scientific
data as if they were repairs. Slice 1 must not imply this richer synchronization
has already been implemented.

## Planned richer versioned protocol

Later contracts should explicitly version capabilities, viewer commands, events,
source/display mappings and scientific revision tokens. Define command responses,
error types, event ordering, subscriptions and shutdown semantics before use.
Mutation/edit events will connect native edits to Forge invalidation; result
publication will reject obsolete task revisions. These are design requirements,
not additional methods on the minimal `Extension` class. Do not assume hot web
callback unregister will be available in a later version either.

## Verification and bug ownership

Test native apps with no extension and with Forge Chat; verify native controls,
shared backend identity, detached snapshots, namespacing, nonblocking read-only
work, missing endpoint errors, cleanup and headless TUI startup. Tests and real
frontend trials are pending evidence, not implied by this document.

Fix generic host/native-view failures in MatterVis, chemistry failures in MCK,
and workflow failures in Forge. Reproduce races with regression tests rather than
sleeps or duplicate viewer state. A relevant upstream fix must become a reachable
upstream commit before the parent pin is shared. See [Upstream](upstream.md).