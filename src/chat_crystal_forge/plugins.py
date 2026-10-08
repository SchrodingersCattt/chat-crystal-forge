"""Optional chat panel for native MatterVis Web and Textual hosts.

All scientific work belongs to ForgeService. Callbacks only submit work or read
snapshots. No replacement viewer, global service or model credentials in components.
"""

from __future__ import annotations

import json

from mat_viewer.extensions import Extension

from .service import ForgeService


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
    if result.get("status") in {"passed", "blocked"} and ("reasons" in result or "message" in result):
        return str(result.get("message") or result.get("reasons"))
    return content


class ForgeChatExtension(Extension):
    """One instance per app. Its service and subscriptions are never shared globally."""

    name = "crystalforge.chat"

    def __init__(self, service: ForgeService):
        self.service = service
        self._timer = None
        self._message_ids: set[str] = set()

    def build_web_panel(self, context):
        from dash import dcc, html

        return html.Section(
            [
                html.Header([
                    html.H2("Chat", id="forge-chat-heading",
                            style={"margin": "0", "fontSize": "20px", "color": "#1E3A5F"}),
                    html.Span("Ready", id="forge-chat-badge", style={"fontSize": "11px", "color": "#0F615B",
                              "background": "#E5F2EF", "borderRadius": "4px", "padding": "3px 6px"}),
                ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"}),
                html.Details([
                    html.Summary("How to use", style={"cursor": "pointer", "color": "#526579"}),
                    html.P("Use /inspect for MCK checks and /list for input IDs. Natural-language "
                           "chat needs a configured model. Checks target registered copies, not "
                           "subsequent native viewer edits; preparation requires explicit scientific decisions."),
                ], style={"fontSize": "12px"}),
                html.Div("Model setup needed" if self.service.settings.configuration_error()
                         else "Model configured", id="forge-chat-model-status",
                         style={"fontSize": "12px", "color": "#526579"}),
                html.Div(id="forge-chat-inputs", style={"fontSize": "12px", "color": "#526579"}),
                html.Div(
                    id="forge-chat-transcript",
                    role="log",
                    style={"flex": "1", "overflowY": "auto", "minHeight": "100px",
                           "paddingRight": "3px"},
                ),
                html.Div(id="forge-chat-status", role="status", style={"fontSize": "12px"}),
                html.Div(id="forge-chat-error", role="alert", style={"color": "#B91C3C"}),
                html.Label("Message", htmlFor="forge-chat-message",
                           style={"fontSize": "12px", "color": "#526579"}),
                dcc.Textarea(
                    id="forge-chat-message", placeholder="Ask about registered structures…",
                    style={"width": "100%", "minHeight": "80px", "fontFamily": "Arial, sans-serif",
                           "fontSize": "14px", "boxSizing": "border-box", "padding": "10px",
                           "border": "1px solid #CBD3DC", "borderRadius": "6px", "resize": "vertical"},
                ),
                html.Button(
                    "Send", id="forge-chat-send", n_clicks=0,
                    style={"background": "#1E3A5F", "color": "white", "padding": "10px",
                           "border": "none", "borderRadius": "5px", "cursor": "pointer"},
                ),
                dcc.Store(id="forge-chat-render-key", data=""),
                dcc.Interval(id="forge-chat-poll", interval=300),
            ],
                 # The native host now contains its diagnostics inside the viewer.
                 style={"height": "100%", "boxSizing": "border-box", "padding": "20px 16px",
                   "display": "flex", "flexDirection": "column", "gap": "10px",
                     "fontFamily": "Arial, sans-serif", "fontSize": "14px",
                     "background": "#F7F9FB", "color": "#374151"},
        )

    def register_web(self, app, context):
        from dash import Input, Output, State, html, no_update
        from dash.exceptions import PreventUpdate

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
            Output("forge-chat-render-key", "data"),
            Input("forge-chat-poll", "n_intervals"), State("forge-chat-render-key", "data"),
        )
        def refresh(_ticks, previous_key):
            snapshot = self.service.snapshot()
            render_key = json.dumps([
                [message["id"] for message in snapshot["messages"][-50:]],
                [item["id"] for item in snapshot["structures"]],
                snapshot["status"], snapshot["busy"],
            ])
            if render_key == previous_key:
                return (no_update,) * 5
            cards = [_web_message(message) for message in snapshot["messages"][-50:]]
            status = "Working…" if snapshot["busy"] else snapshot["status"].capitalize()
            inputs = [html.Div(f"{item['name']} · {item['id'][:8]}") for item in snapshot["structures"]]
            return cards, status, snapshot["busy"], inputs, render_key

    def build_tui_panel(self, context):
        from textual.containers import Vertical
        from textual.widgets import Input, RichLog, Static

        service = self.service

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
                body = tool_summary(message["content"]) if message["role"] == "tool" else message["content"]
                log.write(Text(f"{message['role'].upper()}\n{body}\n"))
            status.update(
                "Working…" if snapshot["busy"] else snapshot["status"]
            )
            input_widget.disabled = snapshot["busy"]

        refresh()
        self._timer = app.set_interval(0.3, refresh)

    def on_tui_unmount(self, app, context):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def close(self):
        self.service.close()


def _web_message(message):
    """Present native inspection fields without turning ordinary chat into logs."""
    from dash import html

    role, content = message["role"], message["content"]
    report = None
    if role == "tool":
        try:
            payload = json.loads(content[content.index("{"):])
            report = payload.get("report") if isinstance(payload, dict) else None
        except (ValueError, TypeError):
            pass
    contents = [html.Div("You" if role == "user" else "Inspection" if isinstance(report, dict)
                         else "Tool" if role == "tool" else "Assistant",
                         style={"fontSize": "12px", "fontWeight": "bold", "color": "#526579",
                                "marginBottom": "7px"})]
    if isinstance(report, dict):
        colors = {"passed": "#0F615B", "failed": "#B91C3C", "blocked": "#875C16", "error": "#B91C3C"}
        rows = []
        for check in report.get("checks", []):
            state = check.get("status", "unknown")
            rows.append(html.Tr([
                html.Td(check["name"].replace("_", " ").capitalize(), style={"padding": "5px 0"}),
                html.Td(state.capitalize(), style={"textAlign": "right", "fontWeight": "bold",
                                                   "color": colors.get(state, "#526579")}),
            ]))
        contents.extend([
            html.Table(html.Tbody(rows), style={"width": "100%", "fontSize": "12px",
                                               "borderCollapse": "collapse"}),
            html.Div("Registered input · read-only", style={"fontSize": "11px", "color": "#526579",
                                                               "marginTop": "8px"}),
        ])
    else:
        contents.append(html.Div(tool_summary(content) if role == "tool" else content,
                                 style={"whiteSpace": "pre-wrap", "overflowWrap": "anywhere",
                                        "fontSize": "14px", "lineHeight": "1.5"}))
    if role == "tool":
        contents.append(html.Details([
            html.Summary("Details & raw result", style={"cursor": "pointer", "color": "#526579"}),
            html.Pre(content, style={"whiteSpace": "pre-wrap", "overflowWrap": "anywhere",
                                     "fontFamily": "Consolas, monospace", "fontSize": "11px"}),
        ], style={"fontSize": "12px", "marginTop": "8px"}))
    return html.Article(contents, style={"padding": "12px", "marginBottom": "10px",
                                         "background": "#EEF3F8" if role == "user" else "white",
                                         "border": "1px solid #E0E6ED", "borderRadius": "8px"})
