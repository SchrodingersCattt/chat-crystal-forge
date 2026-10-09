"""Chat is a functional panel, not a second application-branded column."""

import json

from chat_crystal_forge.config import Settings
from chat_crystal_forge.plugins import ForgeChatExtension, _web_message
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
        assert panel.className == "forge-chat-panel"
        assert panel.style["background"] == "#F8FAFC"
        assert indexed["forge-chat-send"].style["background"] == "#0F766E"
        assert "CrystalForge" not in text(panel)
        assert "registered copies" in text(panel)
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
    assert "Hard clash" in visible and "Failed" in visible
    assert "Formula consistency" in visible and "Blocked" in visible
    assert "Details & raw result" in visible
    assert content in visible
    assert any(item.__class__.__name__ == "Table" for item in nodes(card))


def test_user_message_remains_plain_prose():
    card = _web_message({"role": "user", "content": "What is this structure?"})
    assert "You" in text(card)
    assert "What is this structure?" in text(card)
    assert not any(item.__class__.__name__ == "Pre" for item in nodes(card))
