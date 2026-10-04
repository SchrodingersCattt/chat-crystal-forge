from __future__ import annotations

import io

import pytest

flask = pytest.importorskip("flask")

from chat_crystal_forge.config import Settings  # noqa: E402
from chat_crystal_forge.http import create_app  # noqa: E402


def test_standalone_forge_session_api(tmp_path):
    app = create_app(tmp_path, Settings())
    try:
        client = app.test_client()
        assert client.get("/healthz").get_json()["service"] == "crystalforge"
        created = client.post("/v1/sessions")
        assert created.status_code == 201
        session_id = created.get_json()["session_id"]
        data = b"""data_water\n_cell_length_a 12\n_cell_length_b 12\n_cell_length_c 12\n_cell_angle_alpha 90\n_cell_angle_beta 90\n_cell_angle_gamma 90\n_space_group_name_H-M_alt 'P 1'\nloop_\n_space_group_symop_operation_xyz\n'x,y,z'\nloop_\n_atom_site_label\n_atom_site_type_symbol\n_atom_site_fract_x\n_atom_site_fract_y\n_atom_site_fract_z\n_atom_site_occupancy\nO1 O 0.5 0.5 0.5 1\n"""
        uploaded = client.post(
            f"/v1/sessions/{session_id}/inputs",
            data={"file": (io.BytesIO(data), "water.cif")},
            content_type="multipart/form-data",
        )
        assert uploaded.status_code == 201
        message = client.post(
            f"/v1/sessions/{session_id}/messages",
            json={"text": "/list"},
        )
        assert message.status_code == 202
        app.extensions["forge_sessions"].get(session_id)._future.result(timeout=30)
        snapshot = client.get(f"/v1/sessions/{session_id}").get_json()
        assert snapshot["structures"][0]["name"].endswith("-water.cif")
        assert all("path" not in item for item in snapshot["structures"])
    finally:
        app.extensions["forge_sessions"].close_all()

