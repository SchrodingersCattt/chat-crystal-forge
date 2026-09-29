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
                html.H2("CrystalForge", style={"margin": "0 0 8px", "color": "#1E3A5F"}),
                html.P("Read-only inspection preview", style={"margin": "0 0 8px"}),
                html.P(
                    "Use /inspect to run MCK checks, /list for input IDs, or ask a question "
                    "with a configured model. Checks target registered input copies, not live "
                    "viewer edits. Repairs are not enabled yet.",
                    style={"fontSize": "12px", "color": "#374151"},
                ),
                html.Div(id="forge-chat-inputs", style={"fontSize": "12px"}),
                html.Div(
                    id="forge-chat-transcript",
                    role="log",
                    style={"flex": "1", "overflowY": "auto", "minHeight": "100px"},
                ),
                html.Div(id="forge-chat-status", role="status", style={"fontSize": "12px"}),
                html.Div(id="forge-chat-error", role="alert", style={"color": "#B91C3C"}),
                dcc.Textarea(
                    id="forge-chat-message", placeholder="Ask about registered structures…",
                    style={"width": "100%", "minHeight": "76px", "fontFamily": "Arial, sans-serif"},
                ),
                html.Button(
                    "Send", id="forge-chat-send", n_clicks=0,
                    style={"background": "#1E3A5F", "color": "white", "padding": "10px",
                           "border": "none", "borderRadius": "5px", "cursor": "pointer"},
                ),
                dcc.Store(id="forge-chat-render-key", data=""),
                dcc.Interval(id="forge-chat-poll", interval=300),
            ],
            # Reserve the native host's floating server-log strip at the bottom.
            style={"height": "100%", "boxSizing": "border-box", "padding": "16px 16px 64px",
                   "display": "flex", "flexDirection": "column", "gap": "10px",
                   "fontFamily": "Arial, sans-serif", "background": "#F3F4F6", "color": "#374151"},
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
            cards = []
            for message in snapshot["messages"][-50:]:
                body = tool_summary(message["content"]) if message["role"] == "tool" else message["content"]
                contents = [html.Strong(message["role"].capitalize()),
                            html.Pre(body, style={"whiteSpace": "pre-wrap", "fontFamily": "Consolas, monospace",
                                                  "fontSize": "12px", "overflowWrap": "anywhere"})]
                if message["role"] == "tool":
                    contents.append(html.Details([html.Summary("Full tool record"),
                                                  html.Pre(message["content"], style={"whiteSpace": "pre-wrap", "fontSize": "11px"})]))
                cards.append(html.Div(contents, style={"padding": "10px", "marginBottom": "8px",
                                                       "background": "white", "border": "1px solid #D1D5DB",
                                                       "borderRadius": "6px"}))
            status = "Working…" if snapshot["busy"] else snapshot["status"]
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
                yield Static("CrystalForge · inspection preview\n/inspect · /list · /help", id="forge-chat-title")
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

        def refresh():
            snapshot = self.service.snapshot()
            log = app.query_one("#forge-chat-log", RichLog)
            for message in snapshot["messages"]:
                if message["id"] in self._message_ids:
                    continue
                self._message_ids.add(message["id"])
                body = tool_summary(message["content"]) if message["role"] == "tool" else message["content"]
                log.write(Text(f"{message['role'].upper()}\n{body}\n"))
            app.query_one("#forge-chat-status", Static).update(
                "Working…" if snapshot["busy"] else snapshot["status"]
            )
            app.query_one("#forge-chat-input", Input).disabled = snapshot["busy"]

        refresh()
        self._timer = app.set_interval(0.3, refresh)

    def on_tui_unmount(self, app, context):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def close(self):
        self.service.close()