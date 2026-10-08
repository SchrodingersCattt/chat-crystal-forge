"""Isolated preparation workers for CrystalForge.

The parent service passes only workspace paths and validated JSON parameters to
this module.  Running the worker as ``python -m`` keeps mutable MolCrysKit
objects out of the service thread and gives recovery a clear process boundary.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .mck import add_hydrogens_file, disorder_files


def _result_error(exc: Exception) -> dict[str, Any]:
    return {"status": "failed", "error": type(exc).__name__, "message": str(exc)[:500]}


def run_operation(operation: str, input_path: Path, output_dir: Path, params: dict[str, Any]) -> dict[str, Any]:
    """Execute one validated operation inside the child process."""
    try:
        if operation == "complete_hydrogens":
            output = output_dir / "prepared.cif"
            result = add_hydrogens_file(
                input_path, output,
                reference_formula=params.get("reference_formula"),
            )
            return {"status": "done", "operation": operation, **result}
        if operation == "disorder":
            result = disorder_files(
                input_path, output_dir,
                method=params["method"], count=params["count"],
                random_seed=params.get("random_seed"), coupled=params.get("coupled", False),
            )
            return {"status": "done", "operation": operation, **result}
        raise ValueError(f"unsupported preparation operation: {operation}")
    except Exception as exc:  # child errors are data, never an unhandled protocol line
        return _result_error(exc)


def run_isolated(workspace: Path, input_path: Path, operation: str,
                 params: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Run a preparation operation in a clean Python subprocess."""
    spec = {
        "operation": operation,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "params": params,
    }
    completed = subprocess.run(
        [sys.executable, "-m", "chat_crystal_forge.preparation"],
        input=json.dumps(spec), text=True, capture_output=True,
        cwd=str(workspace), check=False,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(
            item for item in [str(Path(__file__).resolve().parents[1]), os.environ.get("PYTHONPATH", "")] if item
        )},
    )
    if completed.returncode != 0:
        return {"status": "failed", "error": "worker_exit", "returncode": completed.returncode}
    try:
        result = json.loads(completed.stdout.strip())
    except (TypeError, ValueError):
        return {"status": "failed", "error": "invalid_worker_json"}
    return result if isinstance(result, dict) else {"status": "failed", "error": "invalid_worker_result"}


def main() -> int:
    parser = argparse.ArgumentParser(description="CrystalForge isolated preparation worker")
    parser.parse_args()
    try:
        spec = json.load(sys.stdin)
        result = run_operation(
            spec["operation"], Path(spec["input_path"]), Path(spec["output_dir"]),
            spec.get("params") or {},
        )
    except Exception as exc:
        result = _result_error(exc)
    sys.stdout.write(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through run_isolated
    raise SystemExit(main())
