from __future__ import annotations

from typing import Any


class ReferenceCatalog:
    def __init__(self):
        self._map: dict[tuple[str, str], str] = {}

    def register(self, resource_type: str, source_id: str, logical_name: str) -> str:
        self._map[(resource_type, source_id)] = logical_name
        return logical_name

    def resolve(self, resource_type: str, source_id: str) -> str | None:
        return self._map.get((resource_type, source_id))

    def as_migration_map(self) -> dict[str, str]:
        return {f"{resource_type}:{source_id}": logical_name for (resource_type, source_id), logical_name in self._map.items()}
