"""Service tests. Fake-client tests are unit mocks, not live-model evidence."""

import json
import sqlite3
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from chat_crystal_forge.config import Settings
from chat_crystal_forge.service import ForgeService


@pytest.fixture
def cif(tmp_path):
    path = tmp_path / "water source.cif"
    path.write_text("""data_water
_cell_length_a 12
_cell_length_b 12
_cell_length_c 12
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_chemical_formula_moiety 'H2 O'
_space_group_name_H-M_alt 'P 1'
_space_group_IT_number 1
loop_
_space_group_symop_operation_xyz
'x,y,z'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
O1 O 0.5 0.5 0.5 1
H1 H 0.58 0.5 0.5 1
H2 H 0.4799 0.5774 0.5 1
""", encoding="utf-8")
    return path


@pytest.fixture
def service(tmp_path):
    instance = ForgeService(tmp_path / "session", Settings())
    yield instance
    instance.close()


def wait(service):
    """Bounded test-only synchronization, never a sleep/poll in product code."""
    service._future.result(timeout=60)
    assert not service.snapshot()["busy"]
    return service.snapshot()


class FakeClient:
    """Unit mock of chat.completions; intentionally never contacts a provider."""

    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        self.requests.append(kwargs)
        response = next(self.responses)
        if callable(response):
            return response(kwargs)
        if isinstance(response, Exception):
            raise response
        return response


def response(content=None, calls=()):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=list(calls)))])


def call(identifier, name, arguments):
    return SimpleNamespace(id=identifier, function=SimpleNamespace(name=name, arguments=arguments))


def test_registration_is_copy_only_persistent_and_snapshot_detached(service, cif, monkeypatch):
    def forbidden(_path):
        raise AssertionError("Registration must not parse CIFs")

    monkeypatch.setattr("chat_crystal_forge.service.inspect_file", forbidden)
    identifier = service.add_input(cif)
    snapshot = service.snapshot()
    structure = snapshot["structures"][0]
    assert structure["id"] == identifier
    assert structure["report"] is None
    assert Path(structure["path"]).read_bytes() == cif.read_bytes()
    assert Path(structure["path"]).name == f"{identifier}.cif"
    structure["name"] = "mutated snapshot"
    assert service.snapshot()["structures"][0]["name"] == cif.name
    service.close()
    restored = ForgeService(service.workspace, Settings())
    try:
        assert restored.snapshot()["structures"][0]["id"] == identifier
        assert restored.snapshot()["busy"] is False
    finally:
        restored.close()


def test_input_path_validation(service, tmp_path):
    wrong = tmp_path / "wrong.txt"
    wrong.write_text("data_not_a_cif")
    empty = tmp_path / "empty.cif"
    empty.touch()
    directory = tmp_path / "directory.cif"
    directory.mkdir()
    for path in (wrong, empty, directory, tmp_path / "missing.cif"):
        with pytest.raises(ValueError):
            service.add_input(path)
    assert service.snapshot()["structures"] == []


def test_direct_real_mck_inspection_and_sqlite_restore(service, cif):
    service.submit(f'/load "{cif}"')
    loaded = wait(service)
    identifier = loaded["structures"][0]["id"]
    assert loaded["structures"][0]["report"] is None
    turn_id = service.submit(f"/inspect {identifier}")
    assert isinstance(turn_id, str) and turn_id
    inspected = wait(service)
    report = inspected["structures"][0]["report"]
    assert report["status"] == "inspected", report
    assert not report["errors"]
    assert any("[direct tool: inspect_structure]" in item["content"] for item in inspected["messages"])
    service.close()
    restored = ForgeService(service.workspace, Settings())
    try:
        assert restored.snapshot()["structures"] == inspected["structures"]
        assert restored.snapshot()["messages"] == inspected["messages"]
    finally:
        restored.close()


def test_native_commands_without_model(service):
    for command in ("/help", "/list", "/inspect"):
        service.submit(command)
        snapshot = wait(service)
        assert snapshot["error"] is None
        assert any("direct tool" in item["content"] for item in snapshot["messages"])
    service.submit("/inspect not-a-registered-id")
    assert "Unknown structure ID" in wait(service)["error"]
    service.submit("/finish")
    finished = wait(service)
    assert finished["error"] is None
    assert finished["status"] == "blocked"
    assert any("empty_batch" in item["content"] for item in finished["messages"])


def test_missing_configuration_is_actionable_not_fake_chat(service):
    service.submit("Please inspect my structures")
    snapshot = wait(service)
    assert "OPENAI_MODEL" in snapshot["error"]
    assert not any(item["role"] == "tool" for item in snapshot["messages"])


def test_busy_submit_is_rejected_and_close_discards_late_inspection(service, cif, monkeypatch):
    entered, release = threading.Event(), threading.Event()

    def blocked(_path):
        entered.set()
        assert release.wait(timeout=20)
        return {"status": "inspected", "nested": {"count": 1}}

    monkeypatch.setattr("chat_crystal_forge.service.inspect_file", blocked)
    identifier = service.add_input(cif)
    try:
        service.submit(f"/inspect {identifier}")
        assert entered.wait(timeout=10)
        assert service.snapshot()["busy"]
        with pytest.raises(ValueError, match="already running"):
            service.submit("/list")
        service.close()
        closed = service.snapshot()
        service.close()
        release.set()
        service._future.result(timeout=20)
        assert service.snapshot() == closed
        assert closed["structures"][0]["report"] is None
        with pytest.raises(ValueError, match="closed"):
            service.submit("/help")
        with pytest.raises(ValueError, match="closed"):
            service.add_input(cif)
    finally:
        release.set()


def test_interrupted_state_restores_without_replay(tmp_path, cif):
    workspace = tmp_path / "interrupted"
    instance = ForgeService(workspace, Settings())
    instance.add_input(cif)
    instance.close()
    with sqlite3.connect(workspace / "session.sqlite3") as db:
        db.execute("UPDATE state SET value='working' WHERE key='status'")
    restored = ForgeService(workspace, Settings())
    try:
        snapshot = restored.snapshot()
        assert snapshot["status"] == "interrupted"
        assert snapshot["busy"] is False
        assert snapshot["structures"][0]["report"] is None
        assert restored._future is None
    finally:
        restored.close()


def test_unit_mock_natural_tool_roundtrip(tmp_path, cif, monkeypatch):
    client = FakeClient([])
    instance = ForgeService(tmp_path / "session", Settings(model="unit-mock", base_url="http://localhost:8000/v1"), client=client)
    try:
        identifier = instance.add_input(cif)
        monkeypatch.setattr("chat_crystal_forge.service.inspect_file", lambda path: {"status": "blocked", "reason": "unit mock"})
        client.responses = iter([
            response(calls=[call("list-1", "list_structures", "{}")]),
            response(calls=[call("inspect-1", "inspect_structure", json.dumps({"structure_id": identifier}))]),
            response(calls=[call("list-after-inspect", "list_structures", "{}")]),
            response("Inspection is blocked; no repairs were performed."),
        ])
        instance.submit("Inspect the registered structure")
        snapshot = wait(instance)
        assert len(client.requests) == 4
        assert snapshot["structures"][0]["report"]["status"] == "blocked"
        messages = client.requests[-1]["messages"]
        ids = [c["id"] for msg in messages for c in msg.get("tool_calls", [])]
        results = [msg["tool_call_id"] for msg in messages if msg["role"] == "tool"]
        assert ids == results == ["list-1", "inspect-1", "list-after-inspect"]
        assert snapshot["messages"][-1]["content"].startswith("Inspection is blocked")
        snapshot["structures"][0]["report"]["reason"] = "changed"
        assert instance.snapshot()["structures"][0]["report"]["reason"] == "unit mock"
    finally:
        instance.close()


def test_unit_mock_all_calls_get_results_and_paths_are_rejected(tmp_path, monkeypatch):
    def forbidden(_path):
        raise AssertionError("Unregistered model paths must not reach the reader")

    monkeypatch.setattr("chat_crystal_forge.service.inspect_file", forbidden)
    calls = [call("bad-json", "inspect_structure", "{"),
             call("bad-id", "inspect_structure", '{"structure_id":"C:/private.cif"}'),
             call("bad-args", "inspect_structure", '{"path":"C:/private.cif"}'),
             call("unknown", "shell", '{"command":"anything"}'),
             call("extra", "list_structures", '{"path":"anything"}'),
             call("array", "list_structures", '[]')]
    client = FakeClient([response(calls=calls), response("Please register an input with /load.")])
    instance = ForgeService(tmp_path / "session", Settings(api_key="test-key", model="unit-mock"), client=client)
    try:
        instance.submit("Inspect")
        wait(instance)
        results = [message for message in client.requests[-1]["messages"] if message["role"] == "tool"]
        assert len(results) == len(calls)
        assert {message["tool_call_id"] for message in results} == {item.id for item in calls}
        assert all("error" in json.loads(message["content"]) for message in results)
    finally:
        instance.close()


def test_unit_mock_repeated_no_progress_stops_truthfully(tmp_path):
    client = FakeClient([response(calls=[call("first", "list_structures", "{}")]),
                         response(calls=[call("again", "list_structures", "{}"), call("other", "list_structures", "{}")])])
    instance = ForgeService(tmp_path / "session", Settings(api_key="test-key", model="unit-mock"), client=client)
    try:
        instance.submit("Keep inspecting")
        snapshot = wait(instance)
        assert len(client.requests) == 2
        assert "Stopped repeated" in snapshot["messages"][-1]["content"]
        assert len([message for message in snapshot["messages"] if message["role"] == "tool"]) == 3
    finally:
        instance.close()


def test_unit_mock_provider_errors_are_secret_safe(tmp_path):
    settings = Settings(api_key='test-"secret', base_url="https://user:password@example.com/v1", model="unit-mock")
    client = FakeClient([RuntimeError(settings.api_key + " " + settings.base_url)])
    instance = ForgeService(tmp_path / "session", settings, client=client)
    try:
        instance.submit("Please inspect")
        snapshot = wait(instance)
        assert snapshot["error"]
        output = json.dumps(snapshot)
        assert all(secret not in output for secret in ("secret", "password", "example.com"))
        with sqlite3.connect(instance.workspace / "session.sqlite3") as db:
            stored = str(db.execute("SELECT content FROM messages").fetchall())
        assert "password" not in stored and "secret" not in stored
    finally:
        instance.close()


def test_unit_mock_report_credentials_redacted_before_json(tmp_path, cif, monkeypatch):
    secret = 'secret-"with-quote'
    instance = ForgeService(tmp_path / "session", Settings(api_key=secret))
    monkeypatch.setattr("chat_crystal_forge.service.inspect_file", lambda path: {"warning": secret})
    try:
        identifier = instance.add_input(cif)
        instance.submit(f"/inspect {identifier}")
        snapshot = wait(instance)
        assert snapshot["structures"][0]["report"]["warning"] == "[redacted]"
    finally:
        instance.close()


def test_unit_mock_close_discards_late_provider_reply(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def blocked(_request):
        entered.set()
        assert release.wait(timeout=20)
        return response("late reply must be discarded")

    client = FakeClient([blocked])
    instance = ForgeService(tmp_path / "session", Settings(api_key="test-key", model="unit-mock"), client=client)
    try:
        instance.submit("Hello")
        assert entered.wait(timeout=10)
        instance.close()
        before = instance.snapshot()
        release.set()
        instance._future.result(timeout=20)
        assert instance.snapshot() == before
    finally:
        release.set()
        instance.close()


def test_separate_session_directories_do_not_share_state(tmp_path, cif):
    first = ForgeService(tmp_path / "session-a", Settings())
    second = ForgeService(tmp_path / "session-b", Settings())
    try:
        first.add_input(cif)
        assert second.snapshot()["structures"] == []
    finally:
        first.close()
        second.close()