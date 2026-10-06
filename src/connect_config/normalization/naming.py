from __future__ import annotations

import re


def slugify(value: str) -> str:
    value = value or "resource"
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "resource"


class LogicalNameAllocator:
    def __init__(self, resource_type: str):
        self.resource_type = resource_type
        self._used: dict[str, int] = {}

    def allocate(self, name: str) -> str:
        slug = slugify(name)
        base = slug or self.resource_type
        count = self._used.get(base, 0)
        self._used[base] = count + 1
        if count == 0:
            return base
        return f"{base}_{count + 1}"
