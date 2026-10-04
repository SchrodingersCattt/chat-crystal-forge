"""Standalone CrystalForge HTTP SaaS surface.

This module intentionally owns its own session manager and persistence layout.
It does not import or depend on the separate MatterVis SaaS package.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request

from .config import Settings, load_settings
from .service import ForgeService


class ForgeSessionManager:
    def __init__(self, root: Path, settings: Settings | None = None):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.settings = settings or load_settings()
        self.services: dict[str, ForgeService] = {}

    def create(self) -> tuple[str, ForgeService]:
        identifier = uuid4().hex
        service = ForgeService(self.root / identifier, self.settings)
        self.services[identifier] = service
        return identifier, service

    def get(self, identifier: str) -> ForgeService:
        service = self.services.get(identifier)
        if service is None:
            workspace = self.root / identifier
            if not workspace.is_dir() or not (workspace / "session.sqlite3").is_file():
                raise KeyError(identifier)
            service = ForgeService(workspace, self.settings)
            self.services[identifier] = service
        return service

    def close(self, identifier: str) -> None:
        service = self.services.pop(identifier, None)
        if service is not None:
            service.close()

    def close_all(self) -> None:
        for identifier in list(self.services):
            self.close(identifier)


def _public_snapshot(service: ForgeService) -> dict:
    snapshot = service.snapshot()
    snapshot["structures"] = [
        {key: value for key, value in item.items() if key != "path"}
        for item in snapshot.get("structures", [])
    ]
    return snapshot


def create_app(root: str | Path | None = None, settings: Settings | None = None) -> Flask:
    app = Flask(__name__)
    manager = ForgeSessionManager(
        Path(root or os.environ.get("FORGE_ROOT", ".crystalforge")) / "sessions",
        settings,
    )
    app.extensions["forge_sessions"] = manager
    expected_key = os.environ.get("FORGE_API_KEY", "")

    @app.before_request
    def authenticate():
        if request.path == "/healthz":
            return None
        if expected_key and request.headers.get("X-API-Key") != expected_key:
            return jsonify({"error": "invalid or missing FORGE_API_KEY"}), 401
        return None

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True, "service": "crystalforge", "sessions": len(manager.services)})

    @app.post("/v1/sessions")
    def create_session():
        identifier, service = manager.create()
        return jsonify({"session_id": identifier, "snapshot": _public_snapshot(service)}), 201

    def service_for(identifier: str) -> ForgeService:
        try:
            return manager.get(identifier)
        except KeyError:
            from flask import abort

            abort(404, description="unknown session")

    @app.get("/v1/sessions/<identifier>")
    def session_snapshot(identifier: str):
        return jsonify(_public_snapshot(service_for(identifier)))

    @app.post("/v1/sessions/<identifier>/inputs")
    def add_input(identifier: str):
        service = service_for(identifier)
        if "file" not in request.files:
            return jsonify({"error": "multipart field 'file' is required"}), 400
        uploaded = request.files["file"]
        filename = Path(uploaded.filename or "input.cif").name
        if Path(filename).suffix.lower() != ".cif":
            return jsonify({"error": "CrystalForge currently accepts CIF inputs only"}), 400
        data = uploaded.read(100 * 1024 * 1024 + 1)
        if len(data) > 100 * 1024 * 1024:
            return jsonify({"error": "input exceeds 100 MiB limit"}), 413
        incoming = service.workspace / "incoming"
        incoming.mkdir(exist_ok=True)
        path = incoming / f"{uuid4().hex}-{filename}"
        path.write_bytes(data)
        try:
            identifier_value = service.add_input(path)
        except (OSError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        finally:
            path.unlink(missing_ok=True)
        return jsonify({"structure_id": identifier_value, "snapshot": _public_snapshot(service)}), 201

    @app.post("/v1/sessions/<identifier>/messages")
    def submit_message(identifier: str):
        service = service_for(identifier)
        payload = request.get_json(silent=True) or {}
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            return jsonify({"error": "text is required"}), 400
        try:
            turn_id = service.submit(text)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 409
        return jsonify({"turn_id": turn_id, "status": "working"}), 202

    @app.post("/v1/sessions/<identifier>/inspect")
    def inspect(identifier: str):
        service = service_for(identifier)
        try:
            turn_id = service.submit("/inspect")
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 409
        return jsonify({"turn_id": turn_id, "status": "working"}), 202

    @app.delete("/v1/sessions/<identifier>")
    def close_session(identifier: str):
        service_for(identifier)
        manager.close(identifier)
        return jsonify({"closed": True})

    return app

