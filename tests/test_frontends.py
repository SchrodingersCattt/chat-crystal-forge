"""Real native-host integration; no API key or fabricated model response."""

import asyncio
import json
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

from typer.testing import CliRunner

from chat_crystal_forge.cli import app, create_service
from chat_crystal_forge.config import Settings
from chat_crystal_forge.plugins import ForgeChatExtension
from chat_crystal_forge.service import ForgeService


def demo():
    return Path(str(files("chat_crystal_forge").joinpath("resources/demo-water.cif")))


def test_cli_help_does_not_start_viewer():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "tui" in result.output and "ui" in result.output


def test_terminal_path_without_browser_imports():
    code = """
import importlib.abc
import sys
class RejectBrowser(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'dash', 'flask', 'plotly'}:
            raise ImportError('Browser dependency forbidden in terminal path: ' + fullname)
sys.meta_path.insert(0, RejectBrowser())
from mat_viewer.tui.app import CrystalTUI
from mat_viewer.tui.loader_adapter import load_for_tui
from chat_crystal_forge.plugins import ForgeChatExtension
crystal = load_for_tui(sys.argv[1])
assert crystal.atoms
"""
    result = subprocess.run([sys.executable, "-B", "-c", code, str(demo())],
                            capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, result.stderr


def test_service_resumes_without_duplicate_demo(tmp_path):
    first, paths = create_service(None, tmp_path / "session", tmp_path / "missing.env")
    assert len(paths) == 1
    identifier = first.snapshot()["structures"][0]["id"]
    first.close()
    second, paths = create_service(None, tmp_path / "session", tmp_path / "missing.env")
    try:
        assert len(paths) == 1
        assert second.snapshot()["structures"][0]["id"] == identifier
    finally:
        second.close()


def test_native_web_with_chat_returns_layout_and_direct_checks(tmp_path, monkeypatch):
    from mat_viewer.app import create_app

    monkeypatch.setenv("MATTERVIS_PREWARM", "0")
    service = ForgeService(tmp_path / "session", Settings())
    service.add_input(demo())
    extension = ForgeChatExtension(service)
    viewer = create_app(
        preset_path=str(tmp_path / "preset.json"), root_dir=str(tmp_path),
        cif_paths=[str(demo())], extensions=(extension,),
    )
    try:
        client = viewer.server.test_client()
        response = client.get("/_dash-layout")
        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert "forge-chat-transcript" in text and "crystal-graph" in text
        compact_css = client.get("/assets/panel_resize.css")
        compact_js = client.get("/assets/panel_resize.js")
        assert compact_css.status_code == 200
        assert "@media (max-width: 755px)" in compact_css.get_data(as_text=True)
        assert compact_js.status_code == 200
        assert "COMPACT_BREAKPOINT" in compact_js.get_data(as_text=True)
        service.submit("/inspect")
        service._future.result(timeout=40)
        assert service.snapshot()["structures"][0]["report"]["coverage"]["executed"]
        assert viewer.extension_context.viewer is viewer.crystal_backend
        assert any("forge-chat-transcript" in key for key in viewer.callback_map)
        from dash import no_update
        refresh = next(value["callback"].__wrapped__ for key, value in viewer.callback_map.items()
                   if "forge-chat-transcript" in key)
        rendered = refresh(0, "")
        assert len(rendered) == 5
        assert refresh(1, rendered[-1]) == (no_update,) * 5
    finally:
        viewer.close_extensions()
        viewer.crystal_backend.close()
    assert service.snapshot()["status"] == "closed"


def test_native_web_prunes_stale_scene_store(tmp_path, monkeypatch):
    from mat_viewer.app import create_app
    from mat_viewer.scenes import SceneStore

    stale_path = tmp_path / "stale-scenes.json"
    stale_path.write_text(json.dumps({
        "version": 1,
        "active_id": "scene_stale",
        "order": ["scene_stale"],
        "scenes": [{
            "id": "scene_stale",
            "label": "Vanished upload",
            "structure_name": "VANISHED_UPLOAD",
            "state_patch": {},
            "camera": None,
            "created_at": 0.0,
            "updated_at": 0.0,
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(
        SceneStore,
        "default_path",
        classmethod(lambda cls, root_dir: str(stale_path)),
    )

    viewer = create_app(
        preset_path=str(tmp_path / "viewer.json"),
        root_dir=str(tmp_path),
        cif_paths=[str(demo())],
    )
    try:
        scenes = viewer.crystal_backend.scene_options()
        assert scenes
        assert all(item["structure_name"] != "VANISHED_UPLOAD" for item in scenes)
        persisted = json.loads(stale_path.read_text(encoding="utf-8"))
        assert all(
            item["structure_name"] != "VANISHED_UPLOAD"
            for item in persisted["scenes"]
        )
    finally:
        viewer.crystal_backend.close()


def test_native_tui_keeps_viewer_and_routes_chat_input(tmp_path):
    from mat_viewer.tui.app import CrystalTUI
    from mat_viewer.tui.loader_adapter import load_for_tui
    from textual.widgets import Input

    service = ForgeService(tmp_path / "session", Settings())
    service.add_input(demo())
    extension = ForgeChatExtension(service)
    viewer = CrystalTUI(load_for_tui(str(demo())), extensions=(extension,))

    async def run():
        async with viewer.run_test(size=(150, 42)) as pilot:
            await pilot.pause()
            assert viewer.query_one("#canvas")
            field = viewer.query_one("#forge-chat-input", Input)
            field.focus()
            field.value = "/inspect"
            await pilot.press("enter")
            await asyncio.to_thread(service._future.result, timeout=40)
            assert service.snapshot()["structures"][0]["report"]["read_only"] is True
            assert viewer.extension_context.viewer is viewer
            assert field.value == ""

    try:
        asyncio.run(run())
    finally:
        viewer.close_extensions()
    assert service.snapshot()["status"] == "closed"
