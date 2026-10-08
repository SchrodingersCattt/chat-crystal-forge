"""MolCrysKit adapter used by inspection and isolated preparation jobs."""

from __future__ import annotations

import importlib
import json
import math
import warnings
from dataclasses import asdict
from pathlib import Path
from typing import Any


CHECKS = (
    "hard_clash", "intermolecular_clash", "isolated_atoms",
    "hydrogen_presence", "formula_consistency", "bond_distances",
)


def _crystal_from_file(path: Path):
    """Read a crystal without silently resolving disorder."""
    from molcrys_kit.io.cif import read_mol_crystal

    return read_mol_crystal(str(path), resolve_disorder=False)


def file_has_disorder(path: Path) -> bool:
    """Return whether a CIF still contains unresolved disorder sites."""
    from molcrys_kit.io.cif import scan_cif_disorder

    return bool(scan_cif_disorder(str(path)).has_disorder)


def add_hydrogens_file(path: Path, output: Path, *, reference_formula: str | None = None) -> dict:
    """Complete hydrogen placement and write one CIF.

    This function is deliberately small and side-effect limited so it can be
    called from the preparation subprocess.  The caller is responsible for
    deciding whether the formula/moiety is scientifically unambiguous.
    """
    from molcrys_kit.io.output import write_cif
    from molcrys_kit.operations.hydrogen_completion import add_hydrogens

    crystal = _crystal_from_file(Path(path))
    if reference_formula:
        crystal.formula_moiety = reference_formula
    completed = add_hydrogens(crystal, use_formula_moiety=bool(reference_formula or getattr(crystal, "formula_moiety", None)))
    output.parent.mkdir(parents=True, exist_ok=True)
    write_cif(completed, str(output))
    atoms = completed.to_ase()
    return {"output": str(output), "hydrogen_count": atoms.get_chemical_symbols().count("H")}


def disorder_files(path: Path, output_dir: Path, *, method: str, count: int,
                   random_seed: int | None = None, coupled: bool = False) -> dict:
    """Generate bounded ordered replicas and persist their source indices."""
    from molcrys_kit.analysis.disorder.process import generate_ordered_replicas_from_disordered_sites
    from molcrys_kit.io.output import write_cif

    replicas = generate_ordered_replicas_from_disordered_sites(
        filepath=str(path), generate_count=count, method=method,
        random_seed=random_seed, return_kept_indices=True, coupled=coupled,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for index, item in enumerate(replicas):
        crystal, kept = item if isinstance(item, tuple) else (item, None)
        target = output_dir / f"replica-{index:03d}.cif"
        write_cif(crystal, str(target))
        items.append({"path": str(target), "source_indices": _json_safe(kept)})
    signatures = [json.dumps(item.get("source_indices"), sort_keys=True) for item in items]
    return {
        "method": method, "requested_count": count, "returned_count": len(items),
        "distinct_source_indices": len(set(signatures)), "duplicate_count": len(signatures) - len(set(signatures)),
        "items": items, "random_seed": random_seed, "coupled": coupled,
    }


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    raise TypeError("Unsupported inspection result value")


def _valid_reference(value: str | None) -> bool:
    from ase.data import atomic_numbers
    from molcrys_kit.analysis.formula_moiety import parse_moiety_string

    fragments = parse_moiety_string(value)
    return bool(fragments) and all(
        fragment.multiplier > 0 and all(
            element in atomic_numbers and count > 0
            for element, count in fragment.composition.items()
        ) for fragment in fragments or []
    )


def inspect_file(path: Path, reference_formula: str | None = None) -> dict:
    """Inspect an original CIF, never resolve disorder or add hydrogens.

    ``raw`` preserves native CheckResult fields, including native skipped passes.
    ``status``/``coverage`` are authoritative for execution, not that raw boolean.
    A successful inspection is not preparation or batch completion.
    """
    report: dict[str, Any] = {
        "status": "blocked", "read_only": True, "checks": [],
        "coverage": {"required": list(CHECKS), "executed": [], "blocked": list(CHECKS)},
        "disorder": None, "hydrogen": None, "reference_formula": None,
        "reference_source": None, "findings": [], "errors": [], "warnings": [],
        "limitations": [
            "Hydrogen presence does not establish complete hydrogen assignment.",
            "Formula consistency compares element sets, not exact stoichiometry.",
            "This read-only inspection does not perform preparation or certify completion.",
        ],
    }
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        try:
            from pymatgen.io.cif import CifFile
            from molcrys_kit.io.cif import read_mol_crystal, scan_cif_disorder

            path = Path(path)
            if path.suffix.lower() != ".cif" or not path.is_file() or path.stat().st_size == 0:
                raise ValueError("A nonempty CIF file is required")
            # MCK currently chooses the first block and can default missing cells.
            # Refuse those ambiguous inputs instead of silently accepting defaults.
            blocks = CifFile.from_str(path.read_text(encoding="utf-8")).data
            if len(blocks) != 1:
                report["findings"].append("Select exactly one CIF data block before inspection.")
                raise ValueError("Ambiguous CIF blocks")
            data = next(iter(blocks.values())).data
            cell_tags = [f"_cell_length_{axis}" for axis in "abc"] + [
                f"_cell_angle_{angle}" for angle in ("alpha", "beta", "gamma")
            ]
            if any(str(data.get(tag, "")).strip() in {"", ".", "?"} for tag in cell_tags):
                report["findings"].append("Explicit unit-cell parameters are required.")
                raise ValueError("Missing cell")
            disorder = scan_cif_disorder(str(path))
            report["disorder"] = {
                "has_disorder": bool(disorder.has_disorder),
                "occupancies": _json_safe(disorder.occupancies),
                "disorder_groups": _json_safe(disorder.disorder_groups),
                "source_formula_moiety": disorder.formula_moiety,
            }
            if disorder.has_disorder:
                report["findings"].append("Disorder needs preparation; no disorder resolution was performed.")
            crystal = read_mol_crystal(str(path), resolve_disorder=False)
            atoms = crystal.to_ase()
            if len(atoms) == 0:
                raise ValueError("No atoms read")
            hydrogen_count = atoms.get_chemical_symbols().count("H")
            report["hydrogen"] = {"count": hydrogen_count, "present": hydrogen_count > 0, "completeness": "not_assessed"}
            if not hydrogen_count:
                report["findings"].append("No hydrogen atoms found; hydrogen preparation needs review.")
            source = "user" if reference_formula is not None else "source_formula_moiety"
            candidate = reference_formula if reference_formula is not None else disorder.formula_moiety
            valid_reference = _valid_reference(candidate)
            report["reference_formula"] = candidate
            report["reference_source"] = source if candidate else None
            checks = importlib.import_module("molcrys_kit.analysis.sanity_check")
            for name in CHECKS:
                entry: dict[str, Any] = {"name": name, "status": "error", "raw": None, "reason": None}
                try:
                    kwargs = {"reference_formula": candidate if valid_reference else ""} if name == "formula_consistency" else {}
                    result = getattr(checks, f"check_{name}")(crystal, **kwargs)
                    entry["raw"] = _json_safe(asdict(result))
                    reason = None
                    if name == "formula_consistency" and not valid_reference:
                        reason = "invalid_reference" if candidate else "no_reference"
                    elif name == "intermolecular_clash" and atoms.arrays.get("molecule_index") is None:
                        reason = "missing_molecule_index"
                    elif name == "isolated_atoms":
                        # Upstream catches some missing-molecule exceptions as pass.
                        try:
                            molecule_symbols = [mol.get_chemical_symbols() for mol in crystal.molecules]
                            if sum(map(len, molecule_symbols)) != len(atoms):
                                reason = "incomplete_molecule_information"
                        except (AttributeError, TypeError, IndexError):
                            reason = "missing_molecule_information"
                    if "skipped" in result.message.lower() or result.message == "No molecules to check.":
                        reason = reason or "skipped"
                    entry["reason"] = reason
                    entry["status"] = "blocked" if reason else ("passed" if result.passed else "failed")
                except Exception as exc:
                    entry["reason"] = type(exc).__name__
                    report["errors"].append({"stage": name, "type": type(exc).__name__})
                report["checks"].append(entry)
        except Exception as exc:
            report["errors"].append({"stage": "read", "type": type(exc).__name__})
        report["warnings"] = [str(warning.message) for warning in captured]

    found = {entry["name"] for entry in report["checks"]}
    report["checks"].extend(
        {"name": name, "status": "blocked", "raw": None, "reason": "reader_failed"}
        for name in CHECKS if name not in found
    )
    report["coverage"] = {
        "required": list(CHECKS),
        "executed": [entry["name"] for entry in report["checks"] if entry["status"] in {"passed", "failed"}],
        "blocked": [entry["name"] for entry in report["checks"] if entry["status"] not in {"passed", "failed"}],
    }
    if report["coverage"]["blocked"] or report["errors"]:
        report["status"] = "blocked"
    elif report["findings"] or any(entry["status"] == "failed" for entry in report["checks"]):
        report["status"] = "needs_preparation"
    else:
        report["status"] = "inspected"
    return _json_safe(report)
