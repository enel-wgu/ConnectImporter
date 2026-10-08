from __future__ import annotations

import logging
from typing import Any

import boto3

logger = logging.getLogger(__name__)


def _is_resource_not_found(exc: Exception) -> bool:
    if exc is None:
        return False
    text = str(exc).lower()
    code = getattr(getattr(exc, "response", {}), "get", lambda *_: "")("Error", {}).get("Code")
    return (
        "not found" in text
        or "does not exist" in text
        or "resource not found" in text
        or code in {"ResourceNotFoundException", "404", "NotFoundException"}
    )


def build_session(profile: str | None = None, region: str | None = None):
    return boto3.Session(profile_name=profile, region_name=region)


def list_all(client: Any, method: str, result_key: str, **kwargs) -> list[Any]:
    method_fn = getattr(client, method)
    try:
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
    except Exception as exc:
        if _is_resource_not_found(exc):
            logger.warning("Skipping unreadable AWS Connect page for %s: %s", method, exc)
            return []
        raise
