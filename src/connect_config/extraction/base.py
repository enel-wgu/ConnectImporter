from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ExtractionContext:
    client: Any
    instance_id: str


@dataclass
class NormalizationContext:
    catalog: Any
    client: Any
    instance_id: str
    preassigned_names: dict[str, dict[str, str]] = field(default_factory=lambda: {"contact_flow": {}, "contact_flow_module": {}})


class ResourceHandler(Protocol):
    resource_type: str

    def extract(self, ctx: ExtractionContext) -> list[dict[str, Any]]:
        ...

    def normalize(self, raw: list[dict[str, Any]], ctx: NormalizationContext) -> list[Any]:
        ...
