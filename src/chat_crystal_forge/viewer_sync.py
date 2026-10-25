"""Push Forge revisions into the native MatterVis viewer.

Scientific copies stay in the Forge session. This module only binds the active
revision to a native scene through ``context.revisions`` (schema
``mattervis.revisions/v1``): ``register`` opens a scene, ``reload`` replaces one
scene's source, and ``focus`` selects that scene. The optional Structure Catalog
is not used; Forge already stores immutable revisions.

Web ``focus`` needs the initiating page's ``extension-browser-target`` token.
The terminal host omits it. Calls run on a worker so Dash and Textual callbacks
never wait on a write future.

Startup scenes opened by the host (Web ``cif_paths``, or the first TUI crystal)
are treated as already showing that structure's ``load`` revision. Later
operations, exports, session resumes, and ``/load`` after startup go through
the write API.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from concurrent.futures import Future
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

REVISION_NAMESPACE = "crystalforge.chat"
WRITE_TIMEOUT_SECONDS = 30
RETRY_SECONDS = 2.0


@dataclass(frozen=True)
class ViewerAction:
    """One host call. ``scene_id`` is set only for ``reload``."""

    op: str
    revision_id: str
    structure_id: str
    path: str | None = None
    label: str | None = None
    scene_id: str | None = None
    export_ids: tuple[str, ...] = ()


@dataclass
class ViewerSyncState:
    """Mutable bookkeeping for one host. ``plan_viewer_actions`` does not modify it."""

    seeded: set[str] = field(default_factory=set)
    seeded_structures: set[str] = field(default_factory=set)
    presented: set[str] = field(default_factory=set)
    scenes: dict[str, str] = field(default_factory=dict)
    focused: set[str] = field(default_factory=set)
    seen_exports: set[str] = field(default_factory=set)
    retry_after: dict[str, float] = field(default_factory=dict)


def _same_file(left, right) -> bool:
    if not left or not right:
        return False
    try:
        return Path(left).resolve() == Path(right).resolve()
    except OSError:
        return str(left) == str(right)


def _ready_path(revision: dict) -> str | None:
    if not revision or not str(revision.get("sha256") or "").strip():
        return None
    raw = revision.get("path")
    if not raw:
        return None
    path = Path(raw)
    if path.suffix.lower() != ".cif":
        return None
    try:
        if not path.is_file() or path.stat().st_size <= 0:
            return None
    except OSError:
        return None
    return str(path)


def _label(structure: dict, revision: dict) -> str:
    name = str(structure.get("name") or "Structure").strip() or "Structure"
    operation = str(revision.get("operation") or "revision").strip() or "revision"
    token = str(revision.get("id") or "")[:8]
    return f"{name} · {operation} · {token}"


def _fresh_export_ids(snapshot: dict, revision_id: str, seen: set[str]) -> tuple[str, ...]:
    found = []
    for item in snapshot.get("exports") or []:
        export_id = item.get("id")
        if not export_id or item.get("revision_id") != revision_id or item.get("stale"):
            continue
        if export_id not in seen:
            found.append(str(export_id))
    return tuple(found)


def plan_viewer_actions(snapshot: dict, state: ViewerSyncState, *, now: float) -> list[ViewerAction]:
    """Decide register/reload/focus calls for each structure's active revision.

    A seeded ``load`` revision is already on screen and is left alone until a
    new export asks for an explicit binding. Any other ready active revision
    is registered, or reloaded into the structure's known scene, then focused.
    Repeated polls do not focus a revision again unless a new export appears.
    """

    revisions = {item.get("id"): item for item in snapshot.get("revisions") or []}
    actions: list[ViewerAction] = []
    for structure in snapshot.get("structures") or []:
        revision_id = structure.get("revision_id")
        structure_id = structure.get("id")
        revision = revisions.get(revision_id)
        path = _ready_path(revision) if isinstance(revision, dict) else None
        if not revision_id or not structure_id or path is None or not isinstance(revision, dict):
            continue
        if now < state.retry_after.get(revision_id, 0):
            continue
        export_ids = _fresh_export_ids(snapshot, revision_id, state.seen_exports)
        if revision_id in state.presented:
            if revision_id not in state.focused or export_ids:
                actions.append(ViewerAction(
                    "focus", revision_id, structure_id, export_ids=export_ids,
                ))
            continue
        if (
            revision.get("operation") == "load"
            and revision_id in state.seeded
            and not export_ids
        ):
            continue
        scene_id = state.scenes.get(structure_id)
        label = _label(structure, revision)
        if scene_id:
            actions.append(ViewerAction(
                "reload", revision_id, structure_id, path=path, label=label, scene_id=scene_id,
            ))
        else:
            actions.append(ViewerAction(
                "register", revision_id, structure_id, path=path, label=label,
            ))
        actions.append(ViewerAction(
            "focus", revision_id, structure_id, export_ids=export_ids,
        ))
    return actions


def _sync_key(snapshot: dict):
    revisions = tuple(
        (item.get("id"), item.get("sha256"), item.get("operation"), item.get("path"))
        for item in snapshot.get("revisions") or []
    )
    structures = tuple(
        (item.get("id"), item.get("revision_id"))
        for item in snapshot.get("structures") or []
    )
    exports = tuple(
        (item.get("id"), item.get("revision_id"), bool(item.get("stale")))
        for item in snapshot.get("exports") or []
    )
    return (revisions, structures, exports)


def _startup_loads(snapshot: dict) -> tuple[list[str], list[str]]:
    revisions = snapshot.get("revisions") or []
    revision_ids: list[str] = []
    structure_ids: list[str] = []
    for structure in snapshot.get("structures") or []:
        matched = None
        for revision in revisions:
            if revision.get("structure_id") != structure.get("id"):
                continue
            if revision.get("operation") != "load":
                continue
            if _same_file(revision.get("path"), structure.get("path")):
                matched = revision
                break
        if matched is not None and matched.get("id") and structure.get("id"):
            revision_ids.append(matched["id"])
            structure_ids.append(structure["id"])
    return revision_ids, structure_ids


class ViewerSync:
    """Serialize viewer writes for one ForgeChatExtension instance."""

    def __init__(self, service):
        revision_ids, structure_ids = _startup_loads(service.snapshot())
        self._startup_load_ids = revision_ids
        self._startup_load_structures = structure_ids
        self._state = ViewerSyncState(
            seeded=set(revision_ids),
            seeded_structures=set(structure_ids),
        )
        self._context = None
        self._target: str | None = None
        self._lock = threading.Lock()
        self._closed = False
        self._applied_key = None
        self._pending = None
        self._inflight = False
        self._waiters: list[Future] = []
        self.last_error: str | None = None
        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._loop, name="forge-viewer", daemon=True)
        self._thread.start()

    def bind(self, context) -> None:
        """Remember the host and which startup loads it already displayed.

        Web opens every registered input. The terminal host opens the first
        crystal only; further startup inputs are registered after mount.
        """

        with self._lock:
            self._context = context
            if context is None:
                return
            if getattr(context, "frontend", "web") == "tui":
                self._state.seeded = set(self._startup_load_ids[:1])
                self._state.seeded_structures = set(self._startup_load_structures[:1])
            else:
                self._state.seeded = set(self._startup_load_ids)
                self._state.seeded_structures = set(self._startup_load_structures)

    def note_target(self, target) -> None:
        if isinstance(target, str) and target:
            with self._lock:
                self._target = target

    def schedule(self, snapshot: dict) -> Future:
        """Queue a coalesced sync. Safe to call from a Dash or Textual callback."""

        future: Future = Future()
        try:
            key = _sync_key(snapshot)
            with self._lock:
                if self._closed:
                    future.set_result(None)
                    return future
                if key == self._applied_key and self._settled_locked():
                    future.set_result(None)
                    return future
                self._pending = (snapshot, self._target, self._context)
                self._waiters.append(future)
                if not self._inflight:
                    self._inflight = True
                    self._queue.put(True)
                return future
        except Exception:
            logger.exception("could not schedule MatterVis viewer update")
            if not future.done():
                future.set_result(None)
            return future

    def wait(self, timeout: float = WRITE_TIMEOUT_SECONDS):
        with self._lock:
            waiters = list(self._waiters)
        for future in waiters:
            future.result(timeout)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._pending = None
            waiters = self._waiters
            self._waiters = []
        for future in waiters:
            if not future.done():
                future.set_result(None)
        self._queue.put(None)

    def _loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is None or self._closed:
                return
            try:
                self._drain()
            except Exception:
                logger.exception("MatterVis viewer sync stopped")
                with self._lock:
                    finishing = self._waiters
                    self._waiters = []
                    self._inflight = False
                for future in finishing:
                    if not future.done():
                        future.set_result(None)
                return

    def _settled_locked(self) -> bool:
        now = time.time()
        if self.last_error:
            return False
        if any(when > now for when in self._state.retry_after.values()):
            return False
        if not self._state.presented <= self._state.focused:
            return False
        if len(self._state.seeded_structures) == 1:
            only = next(iter(self._state.seeded_structures))
            if only not in self._state.scenes:
                return False
        return True

    def _drain(self) -> None:
        while True:
            with self._lock:
                pending = self._pending
                self._pending = None
                if pending is None or self._closed:
                    self._inflight = False
                    finishing = self._waiters
                    self._waiters = []
                else:
                    finishing = None
            if finishing is not None:
                for future in finishing:
                    if not future.done():
                        future.set_result(None)
                return
            snapshot, target, context = pending
            failed = False
            bound = context is not None and getattr(context, "revisions", None) is not None
            try:
                if bound:
                    failed = self._apply(snapshot, context, target)
            except Exception as exc:
                failed = True
                with self._lock:
                    self.last_error = str(exc)
                logger.warning("MatterVis viewer sync failed: %s", exc)
            with self._lock:
                if not self._closed and self._pending is not None:
                    continue
                if not self._closed and bound and not failed:
                    self._applied_key = _sync_key(snapshot)
                    self.last_error = None
                self._inflight = False
                if not self._closed and self._pending is not None:
                    self._inflight = True
                    continue
                finishing = self._waiters
                self._waiters = []
            for future in finishing:
                if not future.done():
                    future.set_result(None)
            return

    def _remember_host_scene(self, scene_id) -> None:
        """Associate the single startup structure with the scene the host already opened."""

        if len(self._state.seeded_structures) != 1:
            return
        structure_id = next(iter(self._state.seeded_structures))
        if structure_id in self._state.scenes:
            return
        if isinstance(scene_id, str) and scene_id:
            self._state.scenes[structure_id] = scene_id

    def _apply(self, snapshot: dict, context, target) -> bool:
        """Return True when a write failed and a later poll should retry."""

        if self._closed:
            return False
        host_scene = _host_scene_id(context)
        with self._lock:
            if self._closed:
                return False
            self._remember_host_scene(host_scene)
            actions = plan_viewer_actions(snapshot, self._state, now=time.time())
        failed: set[str] = set()
        saw_failure = False
        for action in actions:
            if action.revision_id in failed and action.op == "focus":
                continue
            with self._lock:
                if self._closed:
                    return saw_failure
            try:
                if action.op == "focus":
                    if self._focus(context, action, target):
                        with self._lock:
                            self._state.focused.add(action.revision_id)
                            self._state.seen_exports.update(action.export_ids)
                            self._state.retry_after.pop(action.revision_id, None)
                else:
                    self._publish(context, action)
            except Exception as exc:
                saw_failure = True
                failed.add(action.revision_id)
                with self._lock:
                    self._state.retry_after[action.revision_id] = time.time() + RETRY_SECONDS
                    self.last_error = f"{action.op} {action.revision_id[:8]}: {exc}"
                logger.warning("MatterVis viewer %s failed: %s", action.op, exc)
        return saw_failure

    def _publish(self, context, action: ViewerAction):
        from mat_viewer.extensions import RevisionId

        revision = RevisionId(REVISION_NAMESPACE, action.revision_id)
        revisions = context.revisions
        try:
            if action.op == "reload":
                future = revisions.reload(revision, action.scene_id, action.path)
            else:
                future = revisions.register(revision, action.path, label=action.label)
            binding = future.result(WRITE_TIMEOUT_SECONDS)
        except KeyError:
            if action.op != "reload":
                raise
            with self._lock:
                self._state.scenes.pop(action.structure_id, None)
            future = revisions.register(revision, action.path, label=action.label or "Structure")
            binding = future.result(WRITE_TIMEOUT_SECONDS)
        except ValueError as exc:
            if "already bound" not in str(exc) and "pending" not in str(exc):
                raise
            binding = revisions.lookup(revision)
        scene_id = binding.scene.scene_id
        with self._lock:
            self._state.presented.add(action.revision_id)
            self._state.scenes[action.structure_id] = scene_id
            self._state.retry_after.pop(action.revision_id, None)
        return scene_id

    def _focus(self, context, action: ViewerAction, target) -> bool:
        """Return False when Web focus is waiting for a page token."""

        from mat_viewer.extensions import RevisionId

        revision = RevisionId(REVISION_NAMESPACE, action.revision_id)
        kwargs = {}
        if getattr(context, "frontend", "web") == "web":
            if not isinstance(target, str) or not target:
                return False
            kwargs["target"] = target
        try:
            context.revisions.focus(revision, **kwargs).result(WRITE_TIMEOUT_SECONDS)
        except KeyError:
            with self._lock:
                self._state.presented.discard(action.revision_id)
                self._state.focused.discard(action.revision_id)
                self._state.scenes.pop(action.structure_id, None)
            raise
        return True


def _host_scene_id(context):
    try:
        return (context.snapshot() or {}).get("scene_id")
    except Exception:
        logger.debug("MatterVis snapshot was not readable", exc_info=True)
        return None
