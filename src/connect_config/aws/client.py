from __future__ import annotations

from typing import Any

import boto3


def build_session(profile: str | None = None, region: str | None = None):
    return boto3.Session(profile_name=profile, region_name=region)


def list_all(client: Any, method: str, result_key: str, **kwargs) -> list[Any]:
    method_fn = getattr(client, method)
    if hasattr(client, "get_paginator"):
        paginator = client.get_paginator(method)
        pages = paginator.paginate(**kwargs)
        items: list[Any] = []
        for page in pages:
            values = page.get(result_key, [])
            if isinstance(values, list):
                items.extend(values)
            else:
                items.append(values)
        return items
    response = method_fn(**kwargs)
    values = response.get(result_key, [])
    if isinstance(values, list):
        return values
    return [values] if values else []
