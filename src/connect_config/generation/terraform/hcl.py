from __future__ import annotations

import json
from typing import Any


def tf_string(value: Any) -> str:
    return json.dumps(value)


def attr(key: str, python_value: Any) -> str:
    return f"  {key} = {tf_string(python_value)}\n"


def attr_raw(key: str, expr: str) -> str:
    return f"  {key} = {expr}\n"


def resource(name: str, resource_type: str, body: list[str]) -> str:
    lines = [f'resource "{resource_type}" "{name}" {{']
    lines.extend(body)
    lines.append("}")
    return "\n".join(lines) + "\n"


def data_source(name: str, data_type: str, body: list[str]) -> str:
    lines = [f'data "{data_type}" "{name}" {{']
    lines.extend(body)
    lines.append("}")
    return "\n".join(lines) + "\n"


def string_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(tf_string(value) for value in values) + "]"
