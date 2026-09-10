"""Persistent, rebuildable tool index for the framework.

The index stores discoverable metadata and entry point references. It never
loads a plugin factory during discovery. Plugin code is loaded only by a future
execution supervisor after a tool has been selected and validated.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from importlib import metadata as importlib_metadata
from pathlib import Path
import sqlite3
import sys
from typing import Any, Iterable

from .models import CONTRACT_VERSION, ToolMetadata
from .registry import ToolSpec, load_registry

ENTRY_POINT_GROUP = "content_skills_toolkit.tools"
INDEX_SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class IndexedTool:
    tool_id: str
    name: str
    description: str
    version: str
    distribution: str
    distribution_version: str
    entry_point_group: str
    entry_point_name: str | None
    object_ref: str | None
    phase: str | None
    script: str | None
    input_schema: str | None
    output_schema: str | None
    contract_version: str
    capabilities: tuple[str, ...]
    input_kinds: tuple[str, ...]
    output_formats: tuple[str, ...]
    tags: tuple[str, ...]
    status: str
    metadata_digest: str
    indexed_at: str

    def to_metadata(self) -> ToolMetadata:
        if not self.input_schema or not self.output_schema:
            raise ValueError(f"{self.tool_id} aún no tiene metadatos contractuales cargados")
        return ToolMetadata(
            id=self.tool_id,
            version=self.version,
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            contract_version=self.contract_version,
            phase=self.phase,
            entrypoint=self.object_ref,
            script=self.script,
            capabilities=frozenset(self.capabilities),
            input_kinds=frozenset(self.input_kinds),
            output_formats=frozenset(self.output_formats),
            tags=frozenset(self.tags),
        )


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _distribution_name(distribution: Any) -> str:
    return str(distribution.metadata.get("Name", "unknown-distribution"))


def _distribution_location(distribution: Any) -> str:
    return str(distribution.locate_file(""))


def discover_external_entry_points(group: str = ENTRY_POINT_GROUP) -> list[dict[str, str]]:
    """Read entry point declarations without loading their objects."""
    selected = importlib_metadata.entry_points()
    if hasattr(selected, "select"):
        entries = list(selected.select(group=group))
    else:  # Python 3.10 compatibility
        entries = list(selected.get(group, ()))
    discovered: list[dict[str, str]] = []
    for entry in entries:
        distribution = getattr(entry, "dist", None)
        distribution_name = _distribution_name(distribution) if distribution else "unknown-distribution"
        distribution_version = str(getattr(distribution, "version", "unknown")) if distribution else "unknown"
        discovered.append({
            "name": str(entry.name),
            "value": str(entry.value),
            "distribution": distribution_name,
            "distribution_version": distribution_version,
            "location": _distribution_location(distribution) if distribution else "unknown",
        })
    return sorted(discovered, key=lambda item: (item["name"], item["distribution"], item["value"]))


def environment_fingerprint(root: Path, group: str = ENTRY_POINT_GROUP) -> str:
    """Calculate a cheap fingerprint for invalidation, without importing plugins."""
    local_files: list[dict[str, Any]] = []
    for path in sorted((root / "toolkit").glob("phase-*/**/catalog.json")):
        stat = path.stat()
        local_files.append({"path": str(path.relative_to(root)), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    for path in sorted((root / "toolkit").glob("phase-*/**/SKILL.md")):
        stat = path.stat()
        local_files.append({"path": str(path.relative_to(root)), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    return _digest({
        "python": sys.executable,
        "python_version": sys.version,
        "contract_version": CONTRACT_VERSION,
        "group": group,
        "local_files": local_files,
        "entry_points": discover_external_entry_points(group),
    })


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS registry_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tools (
            tool_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            version TEXT NOT NULL,
            distribution TEXT NOT NULL,
            distribution_version TEXT NOT NULL,
            entry_point_group TEXT NOT NULL,
            entry_point_name TEXT,
            object_ref TEXT,
            phase TEXT,
            script TEXT,
            input_schema TEXT,
            output_schema TEXT,
            contract_version TEXT NOT NULL,
            capabilities_json TEXT NOT NULL,
            input_kinds_json TEXT NOT NULL,
            output_formats_json TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            status TEXT NOT NULL,
            metadata_digest TEXT NOT NULL,
            indexed_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tools_phase ON tools(phase);
        CREATE INDEX IF NOT EXISTS idx_tools_distribution ON tools(distribution);
        CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
        CREATE INDEX IF NOT EXISTS idx_tools_entry_point_group ON tools(entry_point_group);
        """
    )


def _record_from_spec(spec: ToolSpec, now: str) -> IndexedTool:
    metadata = ToolMetadata(
        id=spec.identifier,
        version="builtin",
        name=spec.name,
        description=spec.description,
        input_schema=str(spec.folder / "input.example.json"),
        output_schema=str(spec.folder / "output.schema.json"),
        phase=spec.phase,
        script=str(spec.runner.relative_to(spec.runner.parents[3])),
        contract_version=CONTRACT_VERSION,
        tags=(spec.phase, spec.slug),
    )
    digest = _digest(metadata.to_dict())
    return IndexedTool(
        tool_id=metadata.id,
        name=metadata.name,
        description=metadata.description,
        version=metadata.version,
        distribution="content-skills-framework-builtin",
        distribution_version="local",
        entry_point_group="builtin",
        entry_point_name=None,
        object_ref=None,
        phase=metadata.phase,
        script=metadata.script,
        input_schema=metadata.input_schema,
        output_schema=metadata.output_schema,
        contract_version=metadata.contract_version,
        capabilities=tuple(sorted(metadata.capabilities)),
        input_kinds=tuple(sorted(metadata.input_kinds)),
        output_formats=tuple(sorted(metadata.output_formats)),
        tags=tuple(sorted(metadata.tags)),
        status="available",
        metadata_digest=digest,
        indexed_at=now,
    )


def _record_from_entry_point(entry: dict[str, str], now: str) -> IndexedTool:
    tool_id = entry["name"]
    description = f"Entry point proporcionado por {entry['distribution']}"
    digest = _digest(entry)
    return IndexedTool(
        tool_id=tool_id,
        name=tool_id,
        description=description,
        version=entry["distribution_version"],
        distribution=entry["distribution"],
        distribution_version=entry["distribution_version"],
        entry_point_group=ENTRY_POINT_GROUP,
        entry_point_name=entry["name"],
        object_ref=entry["value"],
        phase=None,
        script=None,
        input_schema=None,
        output_schema=None,
        contract_version=CONTRACT_VERSION,
        capabilities=(),
        input_kinds=(),
        output_formats=(),
        tags=(),
        status="discovered",
        metadata_digest=digest,
        indexed_at=now,
    )


def _records(root: Path, group: str) -> list[IndexedTool]:
    now = _utc_now()
    records = [_record_from_spec(spec, now) for spec in load_registry(root)]
    records.extend(_record_from_entry_point(entry, now) for entry in discover_external_entry_points(group))
    by_id: dict[str, IndexedTool] = {}
    for record in records:
        if record.tool_id in by_id:
            previous = by_id[record.tool_id]
            raise ValueError(f"Identificador duplicado en el índice: {record.tool_id} ({previous.distribution}, {record.distribution})")
        by_id[record.tool_id] = record
    return sorted(by_id.values(), key=lambda item: item.tool_id)


def _insert_records(connection: sqlite3.Connection, records: Iterable[IndexedTool]) -> None:
    connection.execute("DELETE FROM tools")
    for record in records:
        connection.execute(
            """INSERT INTO tools VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.tool_id,
                record.name,
                record.description,
                record.version,
                record.distribution,
                record.distribution_version,
                record.entry_point_group,
                record.entry_point_name,
                record.object_ref,
                record.phase,
                record.script,
                record.input_schema,
                record.output_schema,
                record.contract_version,
                _json(record.capabilities),
                _json(record.input_kinds),
                _json(record.output_formats),
                _json(record.tags),
                record.status,
                record.metadata_digest,
                record.indexed_at,
            ),
        )


def rebuild_index(root: Path, path: Path, group: str = ENTRY_POINT_GROUP) -> int:
    """Rebuild an index in a temporary SQLite file and atomically replace it."""
    fingerprint = environment_fingerprint(root, group)
    records = _records(root, group)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    connection = _connect(temporary)
    try:
        _create_schema(connection)
        _insert_records(connection, records)
        connection.execute("INSERT OR REPLACE INTO registry_state(key, value) VALUES (?, ?)", ("index_schema_version", INDEX_SCHEMA_VERSION))
        connection.execute("INSERT OR REPLACE INTO registry_state(key, value) VALUES (?, ?)", ("environment_fingerprint", fingerprint))
        connection.execute("INSERT OR REPLACE INTO registry_state(key, value) VALUES (?, ?)", ("indexed_at", _utc_now()))
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Índice SQLite inválido: {integrity}")
    finally:
        connection.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.replace(path)
    return len(records)


def index_is_current(root: Path, path: Path, group: str = ENTRY_POINT_GROUP) -> bool:
    if not path.is_file():
        return False
    try:
        connection = _connect(path)
        _create_schema(connection)
        row = connection.execute("SELECT value FROM registry_state WHERE key = ?", ("environment_fingerprint",)).fetchone()
        stored = row[0] if row else None
        current = environment_fingerprint(root, group)
        return stored == current
    except (OSError, sqlite3.DatabaseError):
        return False
    finally:
        try:
            connection.close()
        except UnboundLocalError:
            pass


def ensure_index(root: Path, path: Path, group: str = ENTRY_POINT_GROUP) -> tuple[Path, bool]:
    rebuilt = False
    if not index_is_current(root, path, group):
        rebuild_index(root, path, group)
        rebuilt = True
    return path, rebuilt


def _row_to_record(row: sqlite3.Row) -> IndexedTool:
    return IndexedTool(
        tool_id=row["tool_id"],
        name=row["name"],
        description=row["description"],
        version=row["version"],
        distribution=row["distribution"],
        distribution_version=row["distribution_version"],
        entry_point_group=row["entry_point_group"],
        entry_point_name=row["entry_point_name"],
        object_ref=row["object_ref"],
        phase=row["phase"],
        script=row["script"],
        input_schema=row["input_schema"],
        output_schema=row["output_schema"],
        contract_version=row["contract_version"],
        capabilities=tuple(json.loads(row["capabilities_json"])),
        input_kinds=tuple(json.loads(row["input_kinds_json"])),
        output_formats=tuple(json.loads(row["output_formats_json"])),
        tags=tuple(json.loads(row["tags_json"])),
        status=row["status"],
        metadata_digest=row["metadata_digest"],
        indexed_at=row["indexed_at"],
    )


def lookup(path: Path, tool_id: str) -> IndexedTool | None:
    connection = _connect(path)
    try:
        _create_schema(connection)
        row = connection.execute("SELECT * FROM tools WHERE tool_id = ?", (tool_id,)).fetchone()
        return _row_to_record(row) if row else None
    finally:
        connection.close()


def list_index(path: Path, phase: str | None = None) -> list[IndexedTool]:
    connection = _connect(path)
    try:
        _create_schema(connection)
        if phase is None:
            rows = connection.execute("SELECT * FROM tools ORDER BY tool_id").fetchall()
        else:
            rows = connection.execute("SELECT * FROM tools WHERE phase = ? ORDER BY tool_id", (phase,)).fetchall()
        return [_row_to_record(row) for row in rows]
    finally:
        connection.close()
