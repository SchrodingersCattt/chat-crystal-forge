# CrystalForge implementation plan

## 1. Authority and progress

Canonical engineering plan, consolidated on 2026-09-29. Approval evidence: the
user said **“Start implementation”** after the complete 12-section plan, approving
proceeding with that plan, including reuse of the actual MatterVis UI and TUI.
The template-based [scope](../devpost/scope.md), [PRD](../devpost/prd.md),
[spec](../devpost/spec.md) and [checklist](../devpost/checklist.md) are initially
saved as `status: draft`; main must review their faithful consolidation before
changing status. This is not a request for a second user sign-off.

Only slice 1 is actively being built. No slice, test run, hands-on checkpoint or
final review is certified complete here. The generic MatterVis host patch is under
validation and is not yet published. Build mode is unset pending early first-slice
feedback. No learner experience or personal profile is inferred.

## 2. Product and proof-of-concept boundary

Wet-lab researchers load experimental molecular-crystal CIFs, inspect findings,
authorize supported preparation, and receive processed CIFs plus operation/check
records. The distinctive feature is the shared inspect–repair–validate workflow,
not a replacement chemistry engine or generic chat window. Both native frontends
must eventually support the complete journey. The current slice is read-only:
no repairs, export certification or `finish` tool.

## 3. Existing frontends, optional Forge Chat

Launch `mat-chat ui` and `mat-chat tui` around MatterVis's existing Dash and Textual
applications with an optional Forge Chat extension. Preserve native controls,
structure rendering, selection and camera behavior. Do not recreate viewers from
scene primitives or introduce a second viewer backend. Standalone MatterVis must
remain usable with no Forge dependency. See [Plugin protocol](plugin-protocol.md).

## 4. Shared service and first-slice modules

Use Python >=3.11, Typer, the official OpenAI-compatible SDK and pinned MCK.
Reuse the existing `.venv`, as chosen by the user. Initial first-party modules are
`src/chat_crystal_forge/{cli,config,service,mck,plugins}.py`; main may split them
later when evidence warrants it. The initial public service is
`ForgeService(workspace, settings=None, client=None)` with `add_input(Path)`,
`submit(text) -> turnid`, `snapshot()` and `close()`.

Snapshots are dictionaries containing `messages`, `structures`, `busy`, `error`
and `status`. Frontends consume shared outcomes, not separate scientific policies.
Direct `/load`, `/list`, `/inspect` and `/help` commands are explicit local commands;
they must not masquerade as AI responses. Natural language requires a configured
endpoint and real model execution. Inspection uses actual MCK calls.

## 5. Model loop and bounded authority

Use one coordinating model/session owner with validated domain tool arguments.
Pair tool calls and results faithfully; an assistant turn ending does not complete
a scientific task. Input files and model responses cannot grant tool permissions.
There is no arbitrary shell/Python execution tool. Adopt concepts from
[Learn ShareAI](https://learn.shareai.run/zh/): s01 loop, s03 permissions, s07
on-demand skills, s08 compaction, s11 recovery, s12 task system and s13 background
work. This is conceptual adoption, not shell-agent implementation or code copying.
Later compaction must preserve decisions, policies and executable evidence outside
the prompt. No invented global time, cost or experiment budget is imposed.

## 6. Execution and ownership

Slice 1 uses one background **thread** for read-only model/MCK work, with serialized
service updates and detached snapshots. UI callbacks must remain responsive and
must not mutate shared scientific objects from the worker. Later mutating/heavy
jobs use isolated processes, revision-scoped inputs and stale-result rejection.
Native view state belongs to MatterVis; task/scientific state belongs to Forge.
Source atom IDs are distinct from displayed symmetry/periodic copies. Camera and
selection changes are not scientific edits. Manual edits must invalidate affected
inspection/validation evidence before future repair execution.

## 7. Scientific operations and decisions

Follow [Structure preparation](structure-preparation.md). Inspect without automatic
disorder resolution. Hydrogen completion must handle H-free and partially
hydrogenated inputs. Carry independently agreed formula/moiety references through
revisions. Ask about consequential chemical ambiguity rather than guessing.
For disorder, obtain unresolved `optimal`/`random`/`enumerate` mode and output
count; retain seed, coupling and source-selection provenance. `optimal` is not
energy optimization. Report shortages and duplicates; do not silently enumerate
all possibilities or discard difficult inputs.

## 8. Checks, export and completion

Reuse current MCK sanity criteria with explicit coverage/prerequisite checks.
An empty report, skipped check, exception or missing reference is not a pass.
Hydrogen presence is not complete hydrogen assignment; formula consistency is
element-set agreement, not exact stoichiometry. Requested operations need their
own evidence. Later export must independently reload each actual CIF and apply
the same recorded policy. Only a nonempty batch with every input's agreed delivery
set accounted for and all required checks actually passed can finish. A changed
revision or policy invalidates earlier evidence. Do not implement `finish` in slice 1.

## 9. Persistence and recovery

SQLite local state is the accepted later persistence choice, with revisioned files
for original inputs and artifacts. Slice 1 need not claim durable jobs or recovery.
Later records cover sessions, turns, inputs, revisions, jobs, decisions, checks,
events and exports. Preserve original inputs; restart must expose interrupted jobs
and resume deliberately, never fabricate successful completion or duplicate a
mutating submission. Repeated no-progress attempts become visible blocked states.

## 10. Configuration and dependency ownership

Use ignored local `.env` settings `OPENAI_API_KEY`, `OPENAI_BASE_URL` and
`OPENAI_MODEL`, with process environment precedence. Keys remain in the request
process, never browser payloads, logs or repository history. No silent provider
fallback. TUI/core startup must not import optional browser dependencies.

Forge owns workflow/plugins; MatterVis owns generic host and native-view bugs;
MCK owns chemistry implementation bugs. Fix relevant bugs with regression tests in
the responsible repository, publish a reachable upstream commit, then update the
parent pin after integration validation. No blanket prohibition on relevant
upstream fixes; no sleeps to mask races. This documentation task makes no upstream
changes or publication claims.

## 11. Ordered delivery and verification

The [build checklist](../devpost/checklist.md) is the canonical progress record:

1. Optional host in real MatterVis UI/TUI + shared read-only chat/MCK inspection.
2. Hydrogen completion and strict export/reload.
3. Disorder decision modes and requested delivery counts.
4. Batch jobs, SQLite persistence and recovery.
5. All-pass completion and integrated failure cases in both frontends.
6. Verified installation, documentation/demo and user final review.

After installation in the selected environment, the planned first-slice command is
`python -B -m pytest tests`. It has not been run by this documentation task.
Verify actual upstream imports, native viewer behavior with/without the plugin,
read-only input preservation, malformed input, missing configuration, endpoint
failure, responsiveness and shutdown. Identify mocked model tests separately from
real endpoint smoke tests. Later test export corruption, stale evidence, skipped
checks, ambiguous operations, partial batches and interruption/recovery.

## 12. Review and release evidence

Obtain early user feedback after slice 1 and final hands-on review after the full
journey; do not infer either from implementation permission. Main reviews document
statuses, host compatibility, public snapshot details, install commands and
verification evidence. Real endpoint configuration and redistributable demo data
remain external inputs. A 100-structure demonstration is a target, not a measured
result. Final install/docs/demo, learning wrap-up and app map remain unchecked.
No complete-app, upstream-bug-fix or public-release claim follows from these drafts.