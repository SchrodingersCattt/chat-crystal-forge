"""Launch MatterVis's existing interfaces with an optional Forge panel."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer

from .config import load_settings
from .service import ForgeService

app = typer.Typer(help="CrystalForge: MatterVis with a read-only inspection/chat panel.", no_args_is_help=True)


def create_service(paths: list[Path] | None, session: Path | None, env_file: Path | None):
    chosen = paths or [Path(str(files("chat_crystal_forge").joinpath("resources/demo-water.cif")))]
    workspace = session or Path.cwd() / ".crystalforge" / uuid4().hex
    service = ForgeService(workspace, load_settings(env_file))
    try:
        if paths or not service.snapshot()["structures"]:
            for path in chosen:
                service.add_input(path)
        registered = [Path(item["path"]) for item in service.snapshot()["structures"]]
    except Exception:
        service.close()
        raise
    return service, registered


@app.command()
def ui(
    paths: Annotated[list[Path] | None, typer.Argument(help="CIF inputs; omitted uses synthetic water.")] = None,
    session: Annotated[Path | None, typer.Option(help="Existing session directory to resume.")] = None,
    env_file: Annotated[Path | None, typer.Option(help="Explicit local environment file.")] = None,
    port: Annotated[int, typer.Option(min=1, max=65535)] = 8050,
):
    """Run the native MatterVis browser UI with Forge Chat on the right."""
    try:
        from mat_viewer.app import create_app
        from .plugins import ForgeChatExtension
    except ImportError as exc:
        raise typer.BadParameter("Install the pinned MatterVis submodule with web dependencies and extension support.") from exc
    service, registered = create_service(paths, session, env_file)
    viewer = None
    try:
        viewer = create_app(
            preset_path=str(service.workspace / "viewer.json"),
            root_dir=str(service.workspace),
            cif_paths=[str(path) for path in registered],
            extensions=(ForgeChatExtension(service),),
        )
        typer.echo(f"Session: {service.workspace}\nOpen http://127.0.0.1:{port} · use /inspect for direct MCK checks")
        viewer.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    finally:
        if viewer is not None:
            viewer.close_extensions()
            viewer.crystal_backend.close()
        service.close()


@app.command()
def tui(
    paths: Annotated[list[Path] | None, typer.Argument(help="CIF inputs; omitted uses synthetic water.")] = None,
    session: Annotated[Path | None, typer.Option(help="Existing session directory to resume.")] = None,
    env_file: Annotated[Path | None, typer.Option(help="Explicit local environment file.")] = None,
):
    """Run the native MatterVis terminal UI with Forge Chat; no browser required."""
    try:
        from mat_viewer.tui.app import CrystalTUI
        from mat_viewer.tui.loader_adapter import load_for_tui
        from .plugins import ForgeChatExtension
    except ImportError as exc:
        raise typer.BadParameter("Install the pinned MatterVis submodule with terminal dependencies and extension support.") from exc
    service, registered = create_service(paths, session, env_file)
    viewer = None
    try:
        crystal = load_for_tui(str(registered[0]))
        viewer = CrystalTUI(crystal, extensions=(ForgeChatExtension(service),))
        viewer.run()
    finally:
        if viewer is not None:
            viewer.close_extensions()
        service.close()