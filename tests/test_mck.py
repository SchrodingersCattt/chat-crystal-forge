"""Real MCK integration on synthetic CIFs, plus explicit checker-failure mocks."""

import importlib
import json

from chat_crystal_forge.mck import CHECKS, inspect_file


def write_water(tmp_path, hydrogens=2, *, moiety=True, occupancy="1.0"):
    """Synthetic isolated water in a large P1 cell; no external dataset."""
    path = tmp_path / "water.cif"
    text = """data_water
_cell_length_a 12
_cell_length_b 12
_cell_length_c 12
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_space_group_name_H-M_alt 'P 1'
_space_group_IT_number 1
"""
    if moiety:
        text += "_chemical_formula_moiety 'H2 O'\n"
    text += """loop_
_space_group_symop_operation_xyz
'x,y,z'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
"""
    text += f"O1 O 0.5 0.5 0.5 {occupancy}\n"
    if hydrogens >= 1:
        text += "H1 H 0.58 0.5 0.5 1.0\n"
    if hydrogens >= 2:
        text += "H2 H 0.4799 0.5774 0.5 1.0\n"
    path.write_text(text, encoding="utf-8")
    return path


def check(report, name):
    return next(item for item in report["checks"] if item["name"] == name)


def test_real_water_inspection_preserves_original(tmp_path):
    path = write_water(tmp_path)
    original = path.read_bytes()
    report = inspect_file(path)
    assert not report["errors"], report
    assert set(report["coverage"]["executed"]) == set(CHECKS)
    assert report["status"] == "inspected"
    assert report["reference_source"] == "source_formula_moiety"
    assert report["hydrogen"] == {"count": 2, "present": True, "completeness": "not_assessed"}
    assert path.read_bytes() == original
    json.dumps(report, allow_nan=False)


def test_no_reference_is_not_native_skipped_pass(tmp_path):
    report = inspect_file(write_water(tmp_path, moiety=False))
    formula = check(report, "formula_consistency")
    assert formula["raw"]["passed"] is True
    assert formula["status"] == "blocked"
    assert formula["reason"] == "no_reference"
    assert report["status"] == "blocked"
    assert "formula_consistency" in report["coverage"]["blocked"]


def test_explicit_independent_reference(tmp_path):
    report = inspect_file(write_water(tmp_path, moiety=False), reference_formula="H2 O")
    assert check(report, "formula_consistency")["status"] == "passed"
    assert report["reference_source"] == "user"


def test_invalid_reference_cannot_become_pass(tmp_path):
    report = inspect_file(write_water(tmp_path), reference_formula="not a formula")
    assert check(report, "formula_consistency")["reason"] == "invalid_reference"
    assert report["status"] == "blocked"


def test_no_hydrogen_needs_preparation(tmp_path):
    report = inspect_file(write_water(tmp_path, hydrogens=0))
    assert check(report, "hydrogen_presence")["status"] == "failed"
    assert report["hydrogen"]["present"] is False
    assert report["status"] == "needs_preparation"
    assert any("hydrogen preparation" in message for message in report["findings"])


def test_partial_hydrogen_never_claims_completeness(tmp_path):
    report = inspect_file(write_water(tmp_path, hydrogens=1))
    assert report["hydrogen"]["count"] == 1
    assert check(report, "hydrogen_presence")["status"] == "passed"
    assert report["hydrogen"]["completeness"] == "not_assessed"
    assert "complete" not in report["status"]


def test_disorder_is_scanned_not_resolved(tmp_path):
    report = inspect_file(write_water(tmp_path, occupancy="0.5"))
    assert report["disorder"]["has_disorder"] is True
    assert report["status"] in {"needs_preparation", "blocked"}
    assert any("no disorder resolution" in message for message in report["findings"])


def test_individual_checker_exception_does_not_skip_remaining_checks(tmp_path, monkeypatch):
    module = importlib.import_module("molcrys_kit.analysis.sanity_check")

    def broken(_crystal):
        raise RuntimeError("unit mock checker failure")

    monkeypatch.setattr(module, "check_hard_clash", broken)
    report = inspect_file(write_water(tmp_path))
    assert check(report, "hard_clash")["status"] == "error"
    assert check(report, "hydrogen_presence")["status"] == "passed"
    assert len(report["checks"]) == 6
    assert report["status"] == "blocked"


def test_native_skipped_result_is_blocked(tmp_path, monkeypatch):
    module = importlib.import_module("molcrys_kit.analysis.sanity_check")
    monkeypatch.setattr(module, "check_intermolecular_clash", lambda crystal:
                        module.CheckResult("intermolecular_clash", True, "No molecule_index array; skipped."))
    report = inspect_file(write_water(tmp_path))
    assert check(report, "intermolecular_clash")["raw"]["passed"] is True
    assert check(report, "intermolecular_clash")["status"] == "blocked"


def test_reader_failure_is_blocked(tmp_path):
    path = tmp_path / "broken.cif"
    path.write_text("not valid CIF")
    report = inspect_file(path)
    assert report["status"] == "blocked"
    assert report["errors"]
    assert report["coverage"]["executed"] == []
    assert len(report["checks"]) == 6


def test_multiple_data_blocks_require_selection(tmp_path):
    path = write_water(tmp_path)
    path.write_text(path.read_text() + "\ndata_other\n_cell_length_a 10\n")
    report = inspect_file(path)
    assert report["status"] == "blocked"
    assert any("one CIF data block" in message for message in report["findings"])