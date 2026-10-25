"""Forge revisions drive MatterVis register / reload / focus."""

import asyncio
import json
from concurrent.futures import Future
from importlib.resources import files
from pathlib import Path

from mat_viewer.extensions import RevisionId, RevisionUnavailable

from chat_crystal_forge.config import Settings
from chat_crystal_forge.plugins import ForgeChatExtension
from chat_crystal_forge.service import ForgeService
from chat_crystal_forge.viewer_sync import (
    REVISION_NAMESPACE,
    ViewerSync,
    ViewerSyncState,
    plan_viewer_actions,
)


def demo():
    return Path(str(files("chat_crystal_forge").joinpath("resources/demo-water.cif")))


def _done(value):
    future = Future()
    future.set_result(value)
    return future


class _Scene:
    def __init__(self, scene_id):
        self.scene_id = scene_id


class _Binding:
    def __init__(self, revision, scene_id):
        self.revision = revision
        self.scene = _Scene(scene_id)
        self.source_id = "source-" + revision.token[:8]


class FakeRevisions:
    def __init__(self, *, stale_reload=False):
        self.calls = []
        self.bindings = {}
        self.stale_reload = stale_reload

    def register(self, revision, source, *, format=None, label=None):
        self.calls.append(("register", revision.token, str(source), label))
        binding = _Binding(revision, "scene-" + revision.token[:6])
        self.bindings[revision.token] = binding
        return _done(binding)

    def reload(self, revision, scene, source, *, format=None):
        scene_id = scene if isinstance(scene, str) else scene.scene_id
        self.calls.append(("reload", revision.token, scene_id, str(source)))
        if self.stale_reload:
            raise KeyError("stale scene generation")
        binding = _Binding(revision, scene_id)
        self.bindings[revision.token] = binding
        return _done(binding)

    def focus(self, revision, *, target=None):
        self.calls.append(("focus", revision.token, target))
        if revision.token not in self.bindings:
            raise KeyError(revision.token)
        return _done(None)

    def lookup(self, revision):
        binding = self.bindings.get(revision.token)
        if binding is None:
            raise RevisionUnavailable(revision.token)
        return binding


class FakeContext:
    def __init__(self, frontend="web", scene_id="scene-host"):
        self.frontend = frontend
        self.revisions = FakeRevisions()
        self.scene_id = scene_id

    def snapshot(self):
        return {"frontend": self.frontend, "scene_id": self.scene_id}


def _service(tmp_path, copies=1):
    service = ForgeService(tmp_path / "session", Settings())
    for index in range(copies):
        target = tmp_path / f"input-{index}.cif"
        target.write_bytes(demo().read_bytes())
        service.add_input(target)
    return service


def _activate(snapshot, *, operation, path, revision_id, export_id=None):
    snap = json.loads(json.dumps(snapshot))
    structure = snap["structures"][0]
    snap["revisions"].append({
        "id": revision_id,
        "structure_id": structure["id"],
        "operation": operation,
        "path": str(path),
        "sha256": "abc123",
    })
    structure["revision_id"] = revision_id
    if export_id:
        snap.setdefault("exports", []).append({
            "id": export_id,
            "revision_id": revision_id,
            "path": str(path),
            "stale": False,
        })
    return snap


def test_seeded_load_does_not_rewrite_the_startup_scene(tmp_path):
    service = _service(tmp_path)
    sync = ViewerSync(service)
    context = FakeContext()
    sync.bind(context)
    try:
        sync.note_target("page-token")
        sync.schedule(service.snapshot()).result(10)
        assert context.revisions.calls == []
        structure_id = service.snapshot()["structures"][0]["id"]
        assert sync._state.scenes[structure_id] == "scene-host"
    finally:
        sync.close()
        service.close()


def test_complete_hydrogens_reloads_and_focuses(tmp_path):
    service = _service(tmp_path)
    prepared = tmp_path / "prepared.cif"
    prepared.write_bytes(demo().read_bytes())
    revision_id = "c" * 32
    snap = _activate(
        service.snapshot(), operation="complete_hydrogens", path=prepared, revision_id=revision_id,
    )
    sync = ViewerSync(service)
    context = FakeContext()
    sync.bind(context)
    try:
        sync.note_target("page-token")
        sync.schedule(snap).result(10)
        assert context.revisions.calls == [
            ("reload", revision_id, "scene-host", str(prepared)),
            ("focus", revision_id, "page-token"),
        ]
        sync.schedule(snap).result(10)
        assert len(context.revisions.calls) == 2
    finally:
        sync.close()
        service.close()


def test_export_of_bound_revision_focuses_without_another_write(tmp_path):
    service = _service(tmp_path)
    prepared = tmp_path / "prepared.cif"
    prepared.write_bytes(demo().read_bytes())
    revision_id = "d" * 32
    snap = _activate(
        service.snapshot(), operation="disorder", path=prepared, revision_id=revision_id,
    )
    sync = ViewerSync(service)
    context = FakeContext()
    sync.bind(context)
    try:
        sync.note_target("page-token")
        sync.schedule(snap).result(10)
        exported = json.loads(json.dumps(snap))
        exported["exports"] = [{
            "id": "export-1",
            "revision_id": revision_id,
            "path": str(prepared),
            "stale": False,
        }]
        sync.schedule(exported).result(10)
        assert context.revisions.calls[-1] == ("focus", revision_id, "page-token")
        assert [call[0] for call in context.revisions.calls].count("reload") == 1
        sync.schedule(exported).result(10)
        assert len(context.revisions.calls) == 3
    finally:
        sync.close()
        service.close()


def test_load_after_startup_registers_and_focuses(tmp_path):
    service = _service(tmp_path)
    sync = ViewerSync(service)
    context = FakeContext()
    sync.bind(context)
    try:
        extra = tmp_path / "extra.cif"
        extra.write_bytes(demo().read_bytes())
        service.add_input(extra)
        second = service.snapshot()["structures"][1]["revision_id"]
        sync.note_target("page-token")
        sync.schedule(service.snapshot()).result(10)
        assert any(call[0] == "register" and call[1] == second for call in context.revisions.calls)
        assert ("focus", second, "page-token") in context.revisions.calls
        assert all(call[0] != "reload" for call in context.revisions.calls)
    finally:
        sync.close()
        service.close()


def test_tui_startup_registers_only_structures_the_host_did_not_open(tmp_path):
    service = _service(tmp_path, copies=2)
    sync = ViewerSync(service)
    context = FakeContext(frontend="tui", scene_id="tui-scene")
    sync.bind(context)
    try:
        first = service.snapshot()["structures"][0]
        second = service.snapshot()["structures"][1]["revision_id"]
        sync.schedule(service.snapshot()).result(10)
        assert ("focus", second, None) in context.revisions.calls
        assert any(call[0] == "register" and call[1] == second for call in context.revisions.calls)
        assert not any(call[1] == first["revision_id"] for call in context.revisions.calls)
        assert sync._state.scenes[first["id"]] == "tui-scene"
    finally:
        sync.close()
        service.close()


def test_web_focus_waits_for_a_page_token(tmp_path):
    service = _service(tmp_path)
    sync = ViewerSync(service)
    context = FakeContext()
    sync.bind(context)
    try:
        extra = tmp_path / "extra.cif"
        extra.write_bytes(demo().read_bytes())
        service.add_input(extra)
        second = service.snapshot()["structures"][1]["revision_id"]
        sync.schedule(service.snapshot()).result(10)
        assert any(call[0] == "register" and call[1] == second for call in context.revisions.calls)
        assert not any(call[0] == "focus" for call in context.revisions.calls)
        sync.note_target("page-token")
        sync.schedule(service.snapshot()).result(10)
        assert ("focus", second, "page-token") in context.revisions.calls
    finally:
        sync.close()
        service.close()


def test_stale_scene_reload_falls_back_to_register(tmp_path):
    service = _service(tmp_path)
    prepared = tmp_path / "prepared.cif"
    prepared.write_bytes(demo().read_bytes())
    revision_id = "e" * 32
    snap = _activate(
        service.snapshot(), operation="complete_hydrogens", path=prepared, revision_id=revision_id,
    )
    sync = ViewerSync(service)
    context = FakeContext()
    context.revisions.stale_reload = True
    sync.bind(context)
    try:
        sync.note_target("page-token")
        sync.schedule(snap).result(10)
        kinds = [call[0] for call in context.revisions.calls]
        assert kinds[:3] == ["reload", "register", "focus"]
        assert sync._state.presented == {revision_id}
    finally:
        sync.close()
        service.close()


def test_placeholder_revision_is_not_sent_to_the_viewer():
    state = ViewerSyncState(seeded=set(), scenes={"struct": "scene-1"})
    snapshot = {
        "structures": [{"id": "struct", "name": "demo.cif", "revision_id": "running", "path": "x.cif"}],
        "revisions": [{
            "id": "running",
            "structure_id": "struct",
            "operation": "complete_hydrogens",
            "path": "prepared.cif",
            "sha256": "",
        }],
        "exports": [],
    }
    assert plan_viewer_actions(snapshot, state, now=0) == []


def test_seeded_load_export_reloads_known_scene(tmp_path):
    path = demo()
    state = ViewerSyncState(seeded={"load-1"}, seeded_structures={"struct"}, scenes={"struct": "scene-1"})
    snapshot = {
        "structures": [{
            "id": "struct", "name": "demo.cif", "revision_id": "load-1", "path": str(path),
        }],
        "revisions": [{
            "id": "load-1", "structure_id": "struct", "operation": "load",
            "path": str(path), "sha256": "abc",
        }],
        "exports": [{
            "id": "export-1", "revision_id": "load-1", "path": str(path), "stale": False,
        }],
    }
    actions = plan_viewer_actions(snapshot, state, now=0)
    assert [action.op for action in actions] == ["reload", "focus"]
    assert actions[0].scene_id == "scene-1"
    assert actions[1].export_ids == ("export-1",)


def test_docs_do_not_require_a_manual_viewer_reload():
    root = Path(__file__).resolve().parents[1]
    phrases = (
        "reload the structure in the viewer manually",
        "reload the center Scene yourself",
        "until MatterVis exposes an extension write API",
        "until MatterVis ships an extension",
        "Until #217 lands",
    )
    for relative in (
        "examples/DEMO.md",
        "docs/upstream.md",
        "docs/SLICE6_HANDOFF.md",
        "docs/plugin-protocol.md",
        "src/chat_crystal_forge/plugins.py",
    ):
        text = (root / relative).read_text(encoding="utf-8")
        for phrase in phrases:
            assert phrase not in text


def test_native_web_reload_and_focus_follow_the_active_revision(tmp_path, monkeypatch):
    from mat_viewer.app import create_app

    monkeypatch.setenv("MATTERVIS_PREWARM", "0")
    service = _service(tmp_path)
    extension = ForgeChatExtension(service)
    viewer = create_app(
        preset_path=str(tmp_path / "preset.json"),
        root_dir=str(tmp_path),
        cif_paths=[str(demo())],
        extensions=(extension,),
    )
    try:
        before = list(viewer.crystal_backend.scene_options())
        host_scene = viewer.extension_context.snapshot()["scene_id"]
        assert host_scene
        prepared = tmp_path / "prepared.cif"
        prepared.write_bytes(demo().read_bytes())
        revision_id = "f" * 32
        snap = _activate(
            service.snapshot(), operation="complete_hydrogens", path=prepared, revision_id=revision_id,
        )
        events = []
        viewer.extension_context.structures.subscribe(events.append)
        target = viewer.crystal_backend._extension_structures.new_target()
        extension._viewer.note_target(target)
        extension._viewer.schedule(snap).result(40)
        binding = viewer.extension_context.revisions.lookup(RevisionId(REVISION_NAMESPACE, revision_id))
        assert binding.scene.scene_id == host_scene
        assert len(viewer.crystal_backend.scene_options()) == len(before)
        assert any(event.kind == "reloaded" and event.scene.scene_id == host_scene for event in events)
        assert any(event.kind == "focused" and event.target == target for event in events)
    finally:
        viewer.close_extensions()
        viewer.crystal_backend.close()


def test_native_web_refresh_registers_and_focuses(tmp_path, monkeypatch):
    from mat_viewer.app import create_app

    monkeypatch.setenv("MATTERVIS_PREWARM", "0")
    service = _service(tmp_path)
    extension = ForgeChatExtension(service)
    viewer = create_app(
        preset_path=str(tmp_path / "preset.json"),
        root_dir=str(tmp_path),
        cif_paths=[str(demo())],
        extensions=(extension,),
    )
    try:
        refresh = next(value["callback"].__wrapped__ for key, value in viewer.callback_map.items()
                       if "forge-chat-transcript" in key)
        first = refresh(0, "", None)
        extension._viewer.wait(30)
        before = len(viewer.crystal_backend.scene_options())
        extra = tmp_path / "extra.cif"
        extra.write_bytes(demo().read_bytes())
        service.add_input(extra)
        events = []
        viewer.extension_context.structures.subscribe(events.append)
        target = viewer.crystal_backend._extension_structures.new_target()
        rendered = refresh(1, first[-1], target)
        assert len(rendered) == 6
        extension._viewer.wait(40)
        assert any(event.kind == "registered" for event in events)
        assert any(event.kind == "focused" and event.target == target for event in events)
        assert len(viewer.crystal_backend.scene_options()) == before + 1
    finally:
        viewer.close_extensions()
        viewer.crystal_backend.close()
        service.close()


def test_native_tui_registers_and_focuses_a_later_input(tmp_path):
    from mat_viewer.tui.app import CrystalTUI
    from mat_viewer.tui.loader_adapter import load_for_tui

    service = _service(tmp_path)
    extension = ForgeChatExtension(service)
    viewer = CrystalTUI(load_for_tui(str(demo())), extensions=(extension,))

    async def run():
        async with viewer.run_test(size=(120, 36)) as pilot:
            await pilot.pause()
            extra = tmp_path / "extra.cif"
            extra.write_bytes(demo().read_bytes())
            service.add_input(extra)
            revision_id = service.snapshot()["structures"][-1]["revision_id"]
            events = []
            viewer.extension_context.structures.subscribe(events.append)
            await asyncio.to_thread(extension._viewer.schedule(service.snapshot()).result, 40)
            binding = viewer.extension_context.revisions.lookup(
                RevisionId(REVISION_NAMESPACE, revision_id)
            )
            assert binding.scene.scene_id in viewer.scenes.controllers
            assert viewer.scenes.active_id == binding.scene.scene_id
            assert any(event.kind == "registered" for event in events)
            assert any(event.kind == "focused" for event in events)

    try:
        asyncio.run(run())
    finally:
        viewer.close_extensions()
        service.close()
