# Licensing and commercial use

Status: the owner selected MIT on 2026-09-29. The root [LICENSE](../LICENSE) applies
to this project's original code and documentation; third-party material keeps its
own applicable terms and required notices. This is practical project guidance,
not legal advice.

The initial copyright line names `chat-crystal-forge contributors`, without
inventing an individual's legal name. The owner can specify a preferred attribution
before release. Do not replace upstream copyright notices with this project name.

## What commercial use means here

Permissive open-source licensing is compatible with selling software, offering
paid hosting and building proprietary additions. It also allows other parties
to use the released code commercially. An open-source release is not an exclusive
commercial advantage by itself.

| Choice | Main consequence |
| --- | --- |
| MIT | Short permissive license. Allows commercial use and closed-source derivatives, subject to preserving required notices. No express patent grant like Apache-2.0. |
| Apache-2.0 | Permissive commercial use with an explicit contributor patent license and patent-termination provisions. Requires preserving applicable notices and marking modified files. |
| AGPL-3.0 | Commercial use is allowed, but covered modifications used to provide a network service carry source-offer obligations to interacting users. This is not a ban on competing services. |

MIT was selected for simple reuse. The alternatives above record the tradeoffs
discussed; they are not additional licenses offered by this repository. If the
commercial strategy changes, review rights and compatibility explicitly rather
than assuming MIT restricts competing proprietary or hosted versions.

Dual licensing can be considered when the owner controls the necessary rights.
Do not promise that future contributions or third-party components can be relicensed
at will. Licenses already granted for released copies cannot simply be withdrawn
because a later version becomes commercial. Decide how to handle outside
contributions before making promises about a proprietary edition.

## Upstream reuse

MCK and MatterVis are included as Git submodules, with their repository history,
source identity and pinned commits preserved. [Upstream dependencies](upstream.md)
records the paths and responsibilities. Submodules make reuse explicit; they do
not change licensing obligations. Dependency use and copied/modified source remain
different integration choices and must be documented accurately.

- Preserve required copyright and license notices for copied/adapted code.
- Record dependency versions or source revisions. Identify what this repository
  adds rather than attributing the upstream engines to the new workflow.
- Confirm licenses for transitive dependencies, sample structures, screenshots
  and any redistributed assets. A repository's software license does not by itself
  establish redistribution rights for every scientific dataset inside it.
- Do not edit or publish changes to the upstream repositories without authorization.

On 2026-09-29, MCK revision
`a271cb7eaaf333f7a1e9bfcd4ba89383de609592` had a recognized MIT license.
MatterVis revision `a85cf2ab0771624afef70263069492c3a5914ecb` declared MIT in its
README and `pyproject.toml`, but the inspected source tree had no license-text
file. Confirm the required copyright/license notice before redistributing adapted
components. This records a source-inspection finding, not a claim that permission
is absent or that the user's own work cannot be used.

References: [MIT](https://opensource.org/license/mit),
[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0),
[AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html).