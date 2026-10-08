"""Workflow tests use local MCK and the isolated preparation worker."""

from pathlib import Path

from chat_crystal_forge.config import Settings
from chat_crystal_forge.service import ForgeService


def dap4() -> Path:
    return Path(__file__).parents[1] / "examples" / "structures" / "DAP-4.cif"


def test_ambiguous_hydrogen_decision_and_finish_gate(tmp_path):
    service = ForgeService(tmp_path / "session", Settings())
    try:
        identifier = service.add_input(dap4())
        waiting = service.complete_hydrogens(identifier)
        assert waiting["status"] == "awaiting_decision"
        assert service.finish()["status"] == "blocked"
        completed = service.complete_hydrogens(identifier, "C6 H18 Cl3 N3 O12")
        assert completed["status"] == "done"
        exported = service.export_structure(identifier, "C6 H18 Cl3 N3 O12")
        assert exported["checks"]["reloaded"] is True
        assert exported["checks"]["passed"] is True
        blocked = service.finish()
        assert blocked["status"] == "blocked"
        assert any(item["reason"] == "disorder_unresolved" for item in blocked["reasons"])
        resolved = service.resolve_disorder(identifier, "optimal", 1)
        assert resolved["status"] == "done"
        delivered = service.export_structure(identifier, "C6 H18 Cl3 N3 O12")
        assert delivered["checks"]["reloaded"] is True
        assert delivered["checks"]["passed"] is True
        assert service.finish()["status"] == "passed"
    finally:
        service.close()


def test_disorder_records_requested_and_returned_counts(tmp_path):
    service = ForgeService(tmp_path / "session", Settings())
    try:
        identifier = service.add_input(dap4())
        result = service.resolve_disorder(identifier, "optimal", 1)
        assert result["status"] == "done"
        assert result["requested_count"] == 1
        assert result["returned_count"] >= 1
        assert service.snapshot()["decisions"][0]["mode"] == "optimal"
    finally:
        service.close()


def test_restart_marks_running_job_interrupted(tmp_path):
    service = ForgeService(tmp_path / "session", Settings())
    identifier = service.add_input(dap4())
    with service._connect() as db:
        db.execute("INSERT INTO jobs(id,structure_id,revision_id,operation,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                   ("job", identifier, None, "disorder", "running", 0, 0))
        db.execute("UPDATE state SET value='working' WHERE key='status'")
    service.close()
    restored = ForgeService(tmp_path / "session", Settings())
    try:
        assert restored.snapshot()["status"] == "interrupted"
        assert restored.snapshot()["jobs"][0]["status"] == "interrupted"
        assert restored.snapshot()["structures"][0]["status"] == "interrupted"
    finally:
        restored.close()
