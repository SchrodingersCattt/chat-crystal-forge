"""Chat is a functional panel, not a second application-branded column."""

import json

from chat_crystal_forge.config import Settings
from chat_crystal_forge.plugins import (
    DEFAULT_FONT_SIZE,
    FONT_SIZE_STEPS,
    ForgeChatExtension,
    _web_message,
    font_size_px,
    panel_style,
    parse_tool_message,
)
from chat_crystal_forge.service import ForgeService


def nodes(component):
    if component is None:
        return
    if isinstance(component, (tuple, list)):
        for child in component:
            yield from nodes(child)
    elif hasattr(component, "to_plotly_json"):
        yield component
        yield from nodes(getattr(component, "children", None))


def text(component):
    if isinstance(component, str):
        return component
    if isinstance(component, (list, tuple)):
        return " ".join(text(child) for child in component)
    return text(getattr(component, "children", ""))


def direct_text(component):
    children = getattr(component, "children", None)
    if isinstance(children, str):
        return children
    return ""


def font_sizes(component):
    for item in nodes(component):
        style = getattr(item, "style", None) or {}
        if isinstance(style, dict) and style.get("fontSize"):
            yield getattr(item, "id", None), style["fontSize"]


def assert_tracks_panel_root(component):
    """Child type is em-based so the panel root size scales it. Absolute px does not."""
    for element_id, size in font_sizes(component):
        assert size == "1em" or size.endswith("em / 13)"), (element_id, size)


def test_chat_heading_and_setup_state(tmp_path):
    service = ForgeService(tmp_path / "session", Settings())
    plugin = ForgeChatExtension(service)
    try:
        panel = plugin.build_web_panel(None)
        indexed = {getattr(item, "id", None): item for item in nodes(panel)}
        assert indexed["forge-chat-heading"].children == "Chat"
        assert indexed["forge-chat-model-status"].children == "Model setup needed"
        assert "forge-chat-revisions" in indexed
        assert panel.className == "forge-chat-panel"
        assert panel.style["background"] == "#F8FAFC"
        assert indexed["forge-chat-send"].style["background"] == "#0F766E"
        assert "CrystalForge" not in text(panel)
        assert "registered copies" in text(panel)
        assert "manual" in text(panel).lower() or "reload" in text(panel).lower()
    finally:
        plugin.close()


def test_inspection_card_exposes_failed_and_blocked_checks_and_raw_record():
    payload = {"report": {"checks": [
        {"name": "hard_clash", "status": "failed"},
        {"name": "formula_consistency", "status": "blocked"},
    ]}}
    content = "[direct tool: inspect_structure] " + json.dumps(payload)
    card = _web_message({"role": "tool", "content": content})
    visible = text(card)
    assert "Tool Execution" in visible
    assert "inspect_structure" in visible
    assert "Hard clash" in visible and "Failed" in visible
    assert "Formula consistency" in visible and "Blocked" in visible
    assert "Details & raw result" in visible
    assert content in visible
    assert any(item.__class__.__name__ == "Table" for item in nodes(card))


def test_tool_execution_shows_name_args_status_and_short_result():
    payload = {
        "operation": "disorder",
        "method": "optimal",
        "structure_id": "abcd1234ef",
        "requested_count": 1,
        "returned_count": 1,
        "distinct_source_indices": 1,
        "duplicate_count": 0,
    }
    content = "[direct tool: resolve_disorder] " + json.dumps(payload)
    parsed = parse_tool_message(content)
    assert parsed["name"] == "resolve_disorder"
    assert parsed["args"]["method"] == "optimal"
    assert parsed["status"] == "done"
    card = _web_message({"role": "tool", "content": content})
    visible = text(card)
    assert "Tool Execution" in visible
    assert "resolve_disorder" in visible
    assert "Status" in visible
    assert "Args:" in visible
    assert "optimal" in visible


def test_user_message_remains_plain_prose():
    card = _web_message({"role": "user", "content": "What is this structure?"})
    assert "You" in text(card)
    assert "What is this structure?" in text(card)
    assert "Tool Execution" not in text(card)
    assert not any(item.__class__.__name__ == "Pre" for item in nodes(card))


def test_blocked_finish_card_humanizes_missing_export():
    payload = {
        "status": "blocked",
        "reasons": [{"structure_id": "abcd1234efgh", "reason": "missing_export"}],
    }
    content = "[direct tool: finish_batch] " + json.dumps(payload)
    parsed = parse_tool_message(content)
    assert parsed["status"] == "blocked"
    assert "Finish blocked" in parsed["summary"]
    assert "no certified export yet" in parsed["summary"]
    assert "missing_export" not in parsed["summary"]
    assert "abcd1234" in parsed["summary"]
    card = _web_message({"role": "tool", "content": content})
    visible = text(card)
    assert "Tool Execution" in visible
    assert "Blocked" in visible
    assert "Finish blocked" in visible
    assert "no certified export yet" in visible


def test_awaiting_decision_card_shows_question():
    payload = {
        "status": "awaiting_decision",
        "reason": "formula_reference_required",
        "question": "Confirm an independent formula/moiety before hydrogen completion.",
    }
    content = "[direct tool: complete_hydrogens] " + json.dumps(payload)
    parsed = parse_tool_message(content)
    assert parsed["status"] == "awaiting"
    assert "Awaiting decision" in parsed["summary"]
    card = _web_message({"role": "tool", "content": content})
    visible = text(card)
    assert "Awaiting" in visible
    assert "Confirm an independent formula" in visible


def test_error_tool_card_surfaces_message():
    payload = {"error": "Unknown structure ID. Register the CIF with /load first."}
    content = "[direct tool: resolve_disorder] " + json.dumps(payload)
    parsed = parse_tool_message(content)
    assert parsed["status"] == "error"
    assert "Unknown structure ID" in parsed["summary"]
    card = _web_message({"role": "tool", "content": content})
    assert "Error" in text(card)
    assert "Unknown structure ID" in text(card)


def test_revision_strip_distinguishes_scene_from_versions(tmp_path):
    from chat_crystal_forge.plugins import _revision_strip

    empty = text(_revision_strip({"revisions": [], "structures": []}))
    assert "No revisions yet" in empty
    assert "scientific copies" in empty.lower() or "complete-h" in empty.lower()

    snapshot = {
        "structures": [{"id": "struct01", "revision_id": "revbbbb02"}],
        "revisions": [
            {"id": "revaaaa01", "structure_id": "struct01", "operation": "complete_hydrogens"},
            {"id": "revbbbb02", "structure_id": "struct01", "operation": "disorder"},
        ],
    }
    strip = _revision_strip(snapshot)
    visible = text(strip)
    assert "Scene tabs are not versions" in visible
    assert "disorder" in visible
    assert "revbbbb0" in visible
    assert_tracks_panel_root(strip)
    assert any(
        (getattr(item, "style", None) or {}).get("maxWidth") == "100%"
        for item in nodes(strip)
    )


def test_font_size_control_is_in_the_header_and_persists_locally(tmp_path):
    service = ForgeService(tmp_path / "session", Settings())
    plugin = ForgeChatExtension(service)
    try:
        panel = plugin.build_web_panel(None)
        indexed = {getattr(item, "id", None): item for item in nodes(panel)}
        header_ids = {getattr(item, "id", None) for item in nodes(indexed["forge-chat-header"])}
        control = indexed["forge-chat-font-size"]
        assert "forge-chat-font-control" in header_ids
        assert "forge-chat-font-size" in header_ids
        assert "forge-chat-font-size" not in {
            getattr(item, "id", None) for item in nodes(indexed["forge-chat-transcript"])
        }
        ids = [getattr(item, "id", None) for item in nodes(panel)]
        assert ids.index("forge-chat-font-size") < ids.index("forge-chat-transcript")
        assert ids.index("forge-chat-font-size") < ids.index("forge-chat-message")
        assert control.persistence is True
        assert control.persistence_type == "local"
        assert control.persisted_props == ["value"]
        assert control.value == DEFAULT_FONT_SIZE == "default"
        assert [(item["value"], item["label"]) for item in control.options] == [
            (step, label) for step, label, _size in FONT_SIZE_STEPS
        ]
        assert [font_size_px(step) for step, _label, _size in FONT_SIZE_STEPS] == [
            "12px", "13px", "16px", "18px",
        ]
        assert font_size_px("not-a-step") == "13px"
        assert panel_style("xlarge")["fontSize"] == "18px"
        assert panel_style("xlarge")["minWidth"] == "0"
        assert panel_style("xlarge")["maxWidth"] == "100%"
        assert panel_style(None)["fontSize"] == "13px"
        assert panel.style["fontSize"] == "13px"
        assert panel.style["background"] == "#F8FAFC"
        root_sizes = [size for element_id, size in font_sizes(panel) if element_id == "forge-chat-panel"]
        assert root_sizes == ["13px"]
        for element_id, size in font_sizes(panel):
            if element_id == "forge-chat-panel":
                continue
            assert size == "1em" or size.endswith("em / 13)"), (element_id, size)
        visible = text(panel)
        assert "Text size" in visible
        assert "saved in this browser" in visible
        assert "/inspect" in visible and "/disorder" in visible and "/finish" in visible
        assert any(
            "Slash commands stay available" in direct_text(item)
            and (item.style or {}).get("overflowWrap") == "anywhere"
            for item in nodes(panel)
        )
        assert indexed["forge-chat-message"].style["fontSize"] == "1em"
        assert indexed["forge-chat-send"].style["fontSize"] == "1em"
        assert control.style["flexWrap"] == "wrap"
    finally:
        plugin.close()


def test_font_size_callback_applies_the_selected_step(tmp_path):
    from dash import Dash

    service = ForgeService(tmp_path / "session", Settings())
    plugin = ForgeChatExtension(service)
    app = Dash(__name__)
    app.layout = plugin.build_web_panel(None)
    plugin.register_web(app, None)
    try:
        matches = [
            entry for key, entry in app.callback_map.items()
            if "forge-chat-panel" in str(key) and "style" in str(key)
        ]
        assert len(matches) == 1, list(app.callback_map)
        callback = getattr(matches[0]["callback"], "__wrapped__", matches[0]["callback"])
        assert callback("small")["fontSize"] == "12px"
        assert callback("default")["fontSize"] == "13px"
        assert callback("large")["fontSize"] == "16px"
        largest = callback("xlarge")
        assert largest["fontSize"] == "18px"
        assert largest["overflowY"] == "auto"
        assert callback("nope")["fontSize"] == "13px"
    finally:
        plugin.close()


def test_tool_cards_scale_with_the_panel_and_wrap_at_large_type():
    payload = {"report": {"checks": [
        {"name": "formula_consistency", "status": "blocked"},
        {"name": "hard_clash", "status": "failed"},
    ]}}
    content = "[direct tool: inspect_structure] " + json.dumps(payload)
    card = _web_message({"role": "tool", "content": content})
    assert_tracks_panel_root(card)
    assert any(item.__class__.__name__ == "Table" for item in nodes(card))
    assert any(
        (getattr(item, "style", None) or {}).get("tableLayout") == "fixed"
        for item in nodes(card)
    )
    assert any(
        "Args:" in direct_text(item)
        and (item.style or {}).get("overflowWrap") == "anywhere"
        for item in nodes(_web_message({
            "role": "tool",
            "content": "[direct tool: resolve_disorder] " + json.dumps({
                "operation": "disorder",
                "method": "optimal",
                "structure_id": "abcd1234ef",
                "requested_count": 1,
                "returned_count": 1,
            }),
        }))
    )
    prose = _web_message({"role": "user", "content": "/complete-h abcd1234 C6 H18 Cl3 N3 O12"})
    assert_tracks_panel_root(prose)
    assert any(
        (getattr(item, "style", None) or {}).get("overflowWrap") == "anywhere"
        for item in nodes(prose)
    )
    raw = next(item for item in nodes(card) if item.__class__.__name__ == "Pre")
    assert raw.style["overflowWrap"] == "anywhere"
    assert raw.style["fontSize"].endswith("em / 13)")
