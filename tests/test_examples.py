"""Preserve the owner-supplied input independently of generated outputs."""

import hashlib
from pathlib import Path

from molcrys_kit.io.cif import scan_cif_disorder
from pymatgen.io.cif import CifFile


SOURCE = Path(__file__).resolve().parents[1] / "examples" / "structures" / "DAP-4.cif"


def test_supplied_dap4_is_preserved_byte_for_byte():
    data = SOURCE.read_bytes()
    assert len(data) == 436274
    assert hashlib.sha256(data).hexdigest() == (
        "3967afbcdbded81841ea31c89d2cfdf623c8f3264b208c3c8a2f6ae2a0f9ef5d"
    )


def test_supplied_dap4_is_readable_and_disordered():
    original = SOURCE.read_bytes()
    blocks = CifFile.from_str(original.decode("utf-8")).data
    assert list(blocks) == ["DAP-4"]
    assert blocks["DAP-4"].data["_chemical_formula_sum"].split() == [
        "C6", "H18", "Cl3", "N3", "O12"
    ]
    scan = scan_cif_disorder(str(SOURCE))
    assert scan.has_disorder
    assert any(float(value) < 1 for value in scan.occupancies)
    assert SOURCE.read_bytes() == original