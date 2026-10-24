"""Chat is a functional panel, not a second application-branded column."""

import json

from chat_crystal_forge.config import Settings
from chat_crystal_forge.plugins import (
    ForgeChatExtension,
    _web_message,
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
