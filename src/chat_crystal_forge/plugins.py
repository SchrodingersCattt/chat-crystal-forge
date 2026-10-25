"""Optional chat panel for native MatterVis Web and Textual hosts.

All scientific work belongs to ForgeService. Callbacks only submit work or read
snapshots. No replacement viewer, global service or model credentials in components.
"""

from __future__ import annotations

import json
import re

from mat_viewer.extensions import Extension

from .service import ForgeService
from .viewer_sync import ViewerSync

_TOOL_PREFIX = re.compile(
    r"^\[(?P<source>direct|model) tool:\s*(?P<name>[^;\]]+)(?:;\s*call\s+(?P<call>\S+))?\]\s*"
)
_KEY_ARG_FIELDS = (
    "structure_id", "method", "count", "random_seed", "coupled",
    "reference_formula", "requested_count", "returned_count",
    "hydrogen_count", "export_id", "revision_id",
)


_REASON_LABELS = {
    "missing_export": "no certified export yet — run /export first",
    "disorder_unresolved": "export still contains disorder",
    "checks_not_passed": "export reload checks did not all pass",
    "export_changed": "export file changed after certification (stale)",
    "empty_batch": "no registered structures in this session",
    "formula_reference_required": "confirm an independent formula/moiety",
    "invalid_formula_reference": "provide a parseable formula/moiety",
}


def _reason_label(code: str | None) -> str:
    if not code:
        return "blocked"
    return _REASON_LABELS.get(str(code), str(code))


# Root sizes for the Chat panel text-size control. M (13px) matches the previous
# panel. Child font sizes are em against this 13px base so one root change scales
# messages, tool cards, captions and the composer together.
FONT_SIZE_STEPS: tuple[tuple[str, str, str], ...] = (
    ("small", "S", "12px"),
    ("default", "M", "13px"),
    ("large", "L", "16px"),
    ("xlarge", "XL", "18px"),
)
DEFAULT_FONT_SIZE = "default"
_FONT_ROOT_PX = {step: size for step, _label, size in FONT_SIZE_STEPS}
_FONT_BASE_PX = 13


def font_size_px(step: str | None) -> str:
    """Absolute Chat-panel root size. Unknown steps use the default."""
    return _FONT_ROOT_PX.get(str(step or ""), _FONT_ROOT_PX[DEFAULT_FONT_SIZE])


def _em(px: int) -> str:
    """Design pixel size that tracks the panel root (13px at the default step).

    Set this only on elements whose ancestor font size is the panel root.
    Nested em values would compound.
    """
    if px == _FONT_BASE_PX:
        return "1em"
    return f"calc({px}em / {_FONT_BASE_PX})"


def panel_style(step: str | None = None) -> dict:
    """Chat panel chrome. The host column is about 320px wide, so the pane shrinks and scrolls."""
    return {
        "height": "100%",
        "minHeight": "0",
        "boxSizing": "border-box",
        "padding": "18px 16px 20px",
        "display": "flex",
        "flexDirection": "column",
        "gap": "10px",
        "fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif",
        "fontSize": font_size_px(step),
        "background": "#F8FAFC",
        "color": "#344054",
        "minWidth": "0",
        "maxWidth": "100%",
        "overflowY": "auto",
    }




def parse_tool_message(content: str) -> dict:
    """Split a stored tool message into name, payload, status and short result."""
    match = _TOOL_PREFIX.match(content or "")
    name = (match.group("name").strip() if match else None) or "tool"
    source = match.group("source") if match else "tool"
    remainder = content[match.end():] if match else content
    start = remainder.find("{")
    payload = None
    if start >= 0:
        try:
            payload = json.loads(remainder[start:])
        except (ValueError, TypeError):
            payload = None
    status = _tool_status(payload, remainder if payload is None else None)
    summary = tool_summary(content)
    args = _key_args(payload) if isinstance(payload, dict) else {}
    return {
        "name": name,
        "source": source,
        "payload": payload,
        "status": status,
        "summary": summary,
        "args": args,
    }


def _tool_status(payload, fallback: str | None = None) -> str:
    if not isinstance(payload, dict):
        if fallback and "error" in fallback.lower():
            return "error"
        return "done"
    if "error" in payload:
        return "error"
    if payload.get("status") == "awaiting_decision":
        return "awaiting"
    report = payload.get("report")
    if isinstance(report, dict) and report.get("status"):
        return str(report["status"])
    checks = payload.get("checks")
    if isinstance(checks, dict) and "passed" in checks:
        return "passed" if checks.get("passed") else "blocked"
    if payload.get("status") in {"passed", "blocked", "interrupted", "error"}:
        return str(payload["status"])
    if payload.get("operation"):
        return "done"
    if "structures" in payload:
        return "done"
    return "done"


def _key_args(payload: dict) -> dict:
    args = {}
    for key in _KEY_ARG_FIELDS:
        if key in payload and payload[key] is not None:
            value = payload[key]
            if isinstance(value, str) and len(value) > 48:
                value = value[:8] + "…"
            args[key] = value
    return args


def tool_summary(content: str) -> str:
    """Readable summary; the full native result remains in the stored message."""
    start = content.find("{")
    if start < 0:
        return content
    try:
        result = json.loads(content[start:])
    except (ValueError, TypeError):
        return content
    report = result.get("report")
    if isinstance(report, dict):
        lines = [f"MCK inspection: {report.get('status', 'unknown')}"]
        for check in report.get("checks", []):
            raw = check.get("raw") or {}
            detail = check.get("reason") or raw.get("message", "")
            lines.append(f"{check['name']}: {check['status']} — {detail}")
        lines.extend(report.get("findings", []))
        lines.append("Read-only inspection; no repair or completion certification.")
        return "\n".join(lines)
    if result.get("error"):
        return str(result["error"])
    if "structures" in result:
        return "Registered structures:\n" + "\n".join(
            f"{item['name']} · {item['id']}" for item in result["structures"]
        )
    if result.get("status") == "awaiting_decision":
        return "Awaiting decision: " + str(result.get("question") or result.get("reason"))
    if result.get("operation") == "disorder":
        return (f"Disorder delivery ({result.get('method')}): requested {result.get('requested_count')}, "
                f"returned {result.get('returned_count')}, distinct {result.get('distinct_source_indices')}, "
                f"duplicates {result.get('duplicate_count')}. Optimal is not energy optimization.")
    if result.get("operation") == "complete_hydrogens":
        return f"Hydrogen preparation finished with {result.get('hydrogen_count')} H atoms; export/reload is still required."
    if "checks" in result and "export_id" in result:
        return "Export reload: " + ("passed" if result["checks"].get("passed") else "blocked")
    if result.get("status") == "blocked":
        if result.get("reason"):
            return "Finish blocked: " + _reason_label(result.get("reason"))
        reasons = result.get("reasons")
        if isinstance(reasons, list) and reasons:
            lines = ["Finish blocked:"]
            for item in reasons:
                if not isinstance(item, dict):
                    lines.append("- " + str(item))
                    continue
                sid = str(item.get("structure_id") or "")[:8] or "?"
                lines.append(f"- {sid}: {_reason_label(item.get('reason'))}")
            return "\n".join(lines)
        return "Finish blocked"
    if result.get("status") == "passed" and ("message" in result or "reasons" in result):
        return str(result.get("message") or "All declared inputs certified")
    return content


def _revision_strip(snapshot: dict):
    """Compact revision summary from the session snapshot (not Scene tabs)."""
    from dash import html

    revisions = snapshot.get("revisions") or []
    structures = {item["id"]: item for item in snapshot.get("structures") or []}
    if not revisions:
        return [html.Div(
            "No revisions yet — /complete-h and /disorder create scientific copies here",
            style={"color": "#98A2B3", "fontSize": _em(12), "overflowWrap": "anywhere"},
        )]
    chips = []
    for item in revisions[-8:]:
        current = structures.get(item["structure_id"], {}).get("revision_id") == item["id"]
        label = f"{item.get('operation', 'op')} · {item['id'][:8]}"
        chips.append(html.Span(
            label + (" ★" if current else ""),
            title=f"structure {item.get('structure_id', '')[:8]}",
            style={
                "display": "inline-block", "fontSize": _em(11), "fontWeight": "650",
                "padding": "3px 8px", "margin": "0 4px 4px 0", "borderRadius": "999px",
                "maxWidth": "100%", "boxSizing": "border-box", "overflowWrap": "anywhere",
                "background": "#E7F4F1" if current else "#F2F4F7",
                "color": "#0F615B" if current else "#526579",
                "border": "1px solid #B6E0DA" if current else "1px solid #E4E7EC",
            },
        ))
    return [
        html.Div("Revisions (scientific copies — Scene tabs are not versions)",
                 style={"fontSize": _em(11), "fontWeight": "700", "color": "#667085",
                        "marginBottom": "4px", "overflowWrap": "anywhere"}),
        html.Div(chips),
    ]


def _font_size_control():
    """Header control. Dash persists ``value`` in localStorage for this browser."""
    from dash import dcc, html

    return html.Div(
        [
            html.Span(
                "Text size",
                id="forge-chat-font-label",
                style={"fontSize": _em(12), "fontWeight": "650", "color": "#526579"},
            ),
            dcc.RadioItems(
                id="forge-chat-font-size",
                options=[{"label": label, "value": step} for step, label, _size in FONT_SIZE_STEPS],
                value=DEFAULT_FONT_SIZE,
                inline=True,
                persistence=True,
                persistence_type="local",
                persisted_props=["value"],
                className="forge-chat-font-size",
                inputStyle={"margin": "0 4px 0 0", "accentColor": "#0F766E"},
                labelStyle={
                    "display": "inline-flex",
                    "alignItems": "center",
                    "margin": "0 8px 0 0",
                    "whiteSpace": "nowrap",
                    "cursor": "pointer",
                    "fontSize": "1em",
                },
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "alignItems": "center",
                    "minWidth": "0",
                    "maxWidth": "100%",
                    "fontSize": _em(12),
                },
            ),
        ],
        id="forge-chat-font-control",
        title="Chat text size: S, M (default), L, XL. Saved in this browser.",
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "alignItems": "center",
            "gap": "6px 10px",
            "minWidth": "0",
            "maxWidth": "100%",
        },
    )


class ForgeChatExtension(Extension):
    """One instance per app. Its service and subscriptions are never shared globally."""

    name = "crystalforge.chat"

    def __init__(self, service: ForgeService):
        self.service = service
        self._timer = None
        self._message_ids: set[str] = set()
        self._viewer = ViewerSync(service)

    def build_web_panel(self, context):
        from dash import dcc, html

        self._viewer.bind(context)

        return html.Section(
            [
                html.Header([
                    html.Div([
                        html.H2("Chat", id="forge-chat-heading",
                                style={"margin": "0", "fontSize": _em(18), "fontWeight": "750",
                                       "letterSpacing": "-0.02em", "color": "#172B4D"}),
                        html.Span("Ready", id="forge-chat-badge",
                                  style={"fontSize": _em(11), "fontWeight": "700",
                                         "color": "#146C63", "background": "#E7F4F1",
                                         "borderRadius": "999px", "padding": "4px 8px",
                                         "flexShrink": "0"}),
                    ], style={"display": "flex", "alignItems": "center",
                              "justifyContent": "space-between", "gap": "8px",
                              "flexWrap": "wrap", "minWidth": "0"}),
                    _font_size_control(),
                ], id="forge-chat-header",
                   style={"display": "flex", "flexDirection": "column", "gap": "8px",
                          "paddingBottom": "12px", "borderBottom": "1px solid #D9E2EC",
                          "minWidth": "0"}),
                html.Details([
                    html.Summary("How to use", style={"cursor": "pointer", "color": "#344054",
                                                      "fontWeight": "650"}),
                    html.P(
                        "Text size (S, M, L, XL) is at the top of this panel. M is the default "
                        "and the choice is saved in this browser. Slash commands stay available "
                        "at every size: /inspect, /list, /complete-h, /disorder, /export, /finish "
                        "and /help. Use /inspect for MCK checks and /list for input IDs. "
                        "Natural-language chat needs a configured model. /load, /complete-h, "
                        "/disorder, and /export update registered copies and the center viewer. "
                        "Scene tabs are presentation slots, not scientific versions. "
                        "Preparation requires explicit scientific decisions.",
                        style={"margin": "8px 0 0", "overflowWrap": "anywhere"},
                    ),
                ], style={"fontSize": _em(12), "color": "#667085", "background": "#FFFFFF",
                          "border": "1px solid #E4E7EC", "borderRadius": "8px",
                          "padding": "8px 10px", "minWidth": "0"}),
                html.Div("Model setup needed" if self.service.settings.configuration_error()
                         else "Model configured", id="forge-chat-model-status",
                         style={"fontSize": _em(12), "color": "#526579", "overflowWrap": "anywhere"}),
                html.Div(id="forge-chat-inputs",
                         style={"fontSize": _em(12), "color": "#526579", "overflowWrap": "anywhere",
                                "minWidth": "0"}),
                html.Div(id="forge-chat-revisions",
                         style={"color": "#526579", "background": "#FFFFFF",
                                "border": "1px solid #E4E7EC", "borderRadius": "8px",
                                "padding": "8px 10px", "minWidth": "0"}),
                html.Div(
                    id="forge-chat-transcript",
                    role="log",
                    style={"flex": "1", "overflowY": "auto", "overflowX": "auto",
                           "minHeight": "100px", "minWidth": "0", "paddingRight": "3px"},
                ),
                html.Div(id="forge-chat-status", role="status",
                         style={"fontSize": _em(12), "overflowWrap": "anywhere"}),
                html.Div(id="forge-chat-error", role="alert",
                         style={"color": "#B91C3C", "overflowWrap": "anywhere"}),
                html.Div(
                    [
                        html.Label("Message", htmlFor="forge-chat-message",
                                   style={"fontSize": _em(12), "color": "#526579"}),
                        dcc.Textarea(
                            id="forge-chat-message",
                            placeholder="Ask about registered structures…",
                            style={"width": "100%", "minHeight": "84px", "fontFamily": "inherit",
                                   "fontSize": _em(13), "boxSizing": "border-box", "padding": "11px",
                                   "border": "1px solid #C7D2DF", "borderRadius": "8px",
                                   "resize": "vertical", "background": "#FFFFFF", "color": "#172B4D"},
                        ),
                        html.Button(
                            "Send", id="forge-chat-send", n_clicks=0,
                            style={"background": "#0F766E", "color": "white", "padding": "10px 12px",
                                   "border": "none", "borderRadius": "8px", "cursor": "pointer",
                                   "fontWeight": "700", "fontSize": _em(13), "fontFamily": "inherit"},
                        ),
                    ],
                    id="forge-chat-composer",
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "10px",
                        "flexShrink": "0",
                        "position": "sticky",
                        "bottom": "0",
                        "zIndex": "1",
                        "background": "#F8FAFC",
                        "paddingTop": "4px",
                        "minWidth": "0",
                    },
                ),
                dcc.Store(id="forge-chat-render-key", data=""),
                dcc.Interval(id="forge-chat-poll", interval=300),
            ],
            # The native host contains its diagnostics inside the viewer.
            id="forge-chat-panel",
            className="forge-chat-panel",
            style=panel_style(DEFAULT_FONT_SIZE),
        )

    def register_web(self, app, context):
        from dash import Input, Output, State, html, no_update
        from dash.exceptions import PreventUpdate

        self._viewer.bind(context)

        @app.callback(
            Output("forge-chat-message", "value"), Output("forge-chat-error", "children"),
            Input("forge-chat-send", "n_clicks"), State("forge-chat-message", "value"),
            prevent_initial_call=True,
        )
        def submit(_clicks, message):
            if not message or not message.strip():
                raise PreventUpdate
            try:
                self.service.submit(message)
            except ValueError as exc:
                return no_update, str(exc)
            return "", ""

        @app.callback(
            Output("forge-chat-transcript", "children"), Output("forge-chat-status", "children"),
            Output("forge-chat-send", "disabled"), Output("forge-chat-inputs", "children"),
            Output("forge-chat-revisions", "children"), Output("forge-chat-render-key", "data"),
            Input("forge-chat-poll", "n_intervals"), State("forge-chat-render-key", "data"),
            State("extension-browser-target", "data"),
        )
        def refresh(_ticks, previous_key, browser_target=None):
            snapshot = self.service.snapshot()
            self._viewer.note_target(browser_target)
            self._viewer.schedule(snapshot)
            render_key = json.dumps([
                [message["id"] for message in snapshot["messages"][-50:]],
                [item["id"] for item in snapshot["structures"]],
                [item["id"] for item in snapshot.get("revisions", [])],
                snapshot["status"], snapshot["busy"],
            ])
            if render_key == previous_key:
                return (no_update,) * 6
            cards = [_web_message(message) for message in snapshot["messages"][-50:]]
            status = "Working…" if snapshot["busy"] else snapshot["status"].capitalize()
            inputs = [
                html.Div(f"{item['name']} · {item['id'][:8]}",
                         style={"overflowWrap": "anywhere"})
                for item in snapshot["structures"]
            ]
            return cards, status, snapshot["busy"], inputs, _revision_strip(snapshot), render_key

        @app.callback(
            Output("forge-chat-panel", "style"),
            Input("forge-chat-font-size", "value"),
        )
        def apply_font_size(step):
            return panel_style(step)

    def build_tui_panel(self, context):
        from textual.containers import Vertical
        from textual.widgets import Input, RichLog, Static

        service = self.service
        self._viewer.bind(context)

        class ChatPanel(Vertical):
            DEFAULT_CSS = """
            ChatPanel { height: 1fr; padding: 0 1; }
            #forge-chat-title { height: auto; color: cyan; text-style: bold; }
            #forge-chat-log { height: 1fr; }
            #forge-chat-status { height: 2; }
            #forge-chat-input { dock: bottom; }
            """

            def compose(self):
                yield Static("Chat · inspect and prepare\n/inspect · /complete-h · /disorder · /export · /finish", id="forge-chat-title")
                yield RichLog(id="forge-chat-log", wrap=True, markup=False, highlight=False)
                yield Static("Ready", id="forge-chat-status")
                yield Input(placeholder="Ask or /inspect", id="forge-chat-input")

            def on_input_submitted(self, event: Input.Submitted):
                if event.input.id != "forge-chat-input":
                    return
                event.stop()
                if not event.value.strip():
                    return
                try:
                    service.submit(event.value)
                    event.input.value = ""
                except ValueError as exc:
                    self.query_one("#forge-chat-status", Static).update(str(exc))

        return ChatPanel(id="forge-chat-panel")

    def on_tui_mount(self, app, context):
        from rich.text import Text
        from textual.widgets import Input, RichLog, Static
        from textual.css.query import NoMatches

        self._viewer.bind(context)

        def refresh():
            snapshot = self.service.snapshot()
            try:
                log = app.query_one("#forge-chat-log", RichLog)
                status = app.query_one("#forge-chat-status", Static)
                input_widget = app.query_one("#forge-chat-input", Input)
            except NoMatches:
                # A timer tick can race with Textual unmounting the optional
                # panel. The viewer is already shutting down, so drop this
                # tick and let ``on_tui_unmount`` stop the timer.
                return
            for message in snapshot["messages"]:
                if message["id"] in self._message_ids:
                    continue
                self._message_ids.add(message["id"])
                if message["role"] == "tool":
                    parsed = parse_tool_message(message["content"])
                    args = ", ".join(f"{k}={v}" for k, v in parsed["args"].items()) or "—"
                    body = (
                        f"Tool Execution · {parsed['name']}\n"
                        f"args: {args}\n"
                        f"status: {parsed['status']}\n"
                        f"{parsed['summary']}"
                    )
                else:
                    body = message["content"]
                log.write(Text(f"{message['role'].upper()}\n{body}\n"))
            status.update(
                "Working…" if snapshot["busy"] else snapshot["status"]
            )
            input_widget.disabled = snapshot["busy"]
            self._viewer.schedule(snapshot)

        refresh()
        self._timer = app.set_interval(0.3, refresh)

    def on_tui_unmount(self, app, context):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def close(self):
        self._viewer.close()
        self.service.close()


_STATUS_COLORS = {
    "passed": "#0F615B",
    "failed": "#B91C3C",
    "blocked": "#875C16",
    "error": "#B91C3C",
    "awaiting": "#875C16",
    "done": "#146C63",
}


def _web_message(message):
    """Present tool calls as a Tool Execution panel; keep user/assistant as prose."""
    from dash import html

    role, content = message["role"], message["content"]
    if role != "tool":
        return html.Article([
            html.Div("You" if role == "user" else "Assistant",
                     style={"fontSize": _em(12), "fontWeight": "bold", "color": "#526579",
                            "marginBottom": "7px"}),
            html.Div(content, style={"whiteSpace": "pre-wrap", "overflowWrap": "anywhere",
                                     "fontSize": _em(14), "lineHeight": "1.5"}),
        ], style={"padding": "11px 12px", "marginBottom": "10px",
                  "background": "#EEF7F5" if role == "user" else "#FFFFFF",
                  "border": "1px solid #D9E2EC", "borderRadius": "9px",
                  "boxShadow": "0 1px 2px rgba(23, 43, 77, 0.04)",
                  "minWidth": "0", "maxWidth": "100%", "boxSizing": "border-box"})

    parsed = parse_tool_message(content)
    payload = parsed["payload"] if isinstance(parsed["payload"], dict) else {}
    report = payload.get("report") if isinstance(payload.get("report"), dict) else None
    status = parsed["status"]
    status_color = _STATUS_COLORS.get(status, "#526579")
    arg_bits = [f"{key}={value}" for key, value in parsed["args"].items()]
    contents = [
        html.Div([
            html.Span("Tool Execution", style={"fontWeight": "750", "color": "#172B4D"}),
            html.Span(f" · {parsed['name']}", style={"color": "#526579", "fontWeight": "650"}),
        ], style={"fontSize": _em(12), "marginBottom": "6px", "overflowWrap": "anywhere"}),
        html.Div([
            html.Span("Status ", style={"color": "#667085"}),
            html.Span(status.capitalize(), style={"fontWeight": "750", "color": status_color}),
        ], style={"fontSize": _em(12), "marginBottom": "6px", "overflowWrap": "anywhere"}),
    ]
    if arg_bits:
        contents.append(html.Div(
            "Args: " + ", ".join(arg_bits),
            style={"fontSize": _em(11), "color": "#526579", "marginBottom": "6px",
                   "fontFamily": "Consolas, monospace", "overflowWrap": "anywhere"},
        ))
    if isinstance(report, dict):
        rows = []
        for check in report.get("checks", []):
            state = check.get("status", "unknown")
            rows.append(html.Tr([
                html.Td(check["name"].replace("_", " ").capitalize(),
                        style={"padding": "5px 8px 5px 0", "overflowWrap": "anywhere",
                               "verticalAlign": "top"}),
                html.Td(state.capitalize(), style={"textAlign": "right", "fontWeight": "bold",
                                                   "color": _STATUS_COLORS.get(state, "#526579"),
                                                   "padding": "5px 0 5px 8px",
                                                   "overflowWrap": "anywhere",
                                                   "verticalAlign": "top"}),
            ]))
        contents.extend([
            html.Table([
                html.Colgroup([html.Col(), html.Col(style={"width": "8em"})]),
                html.Tbody(rows),
            ], style={"width": "100%", "fontSize": _em(12),
                      "borderCollapse": "collapse", "tableLayout": "fixed"}),
            html.Div("Registered input · read-only",
                     style={"fontSize": _em(11), "color": "#526579", "marginTop": "8px",
                            "overflowWrap": "anywhere"}),
        ])
    else:
        contents.append(html.Div(parsed["summary"],
                                 style={"whiteSpace": "pre-wrap", "overflowWrap": "anywhere",
                                        "fontSize": _em(13), "lineHeight": "1.45",
                                        "color": "#344054"}))
    contents.append(html.Details([
        html.Summary("Details & raw result", style={"cursor": "pointer", "color": "#526579",
                                                    "fontSize": _em(12)}),
        html.Pre(content, style={"whiteSpace": "pre-wrap", "overflowWrap": "anywhere",
                                 "fontFamily": "Consolas, monospace", "fontSize": _em(11),
                                 "margin": "8px 0 0"}),
    ], style={"marginTop": "8px", "minWidth": "0"}))
    return html.Article(contents, style={"padding": "11px 12px", "marginBottom": "10px",
                                         "background": "#FFFFFF",
                                         "border": "1px solid #D9E2EC", "borderRadius": "9px",
                                         "borderLeft": f"3px solid {status_color}",
                                         "boxShadow": "0 1px 2px rgba(23, 43, 77, 0.04)",
                                         "minWidth": "0", "maxWidth": "100%",
                                         "boxSizing": "border-box"})
