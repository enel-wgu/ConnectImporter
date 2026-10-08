from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import boto3

logger = logging.getLogger(__name__)


class DebuggablePaginator:
    def __init__(self, paginator: Any, output_path: Path, method_name: str):
        self._paginator = paginator
        self._output_path = output_path
        self._method_name = method_name

    def paginate(self, **kwargs):
        pages = self._paginator.paginate(**kwargs)

        def wrapped_pages():
            for page in pages:
                self._write_debug(f"{self._method_name}.paginate", kwargs, page)
                yield page

        return wrapped_pages()

    def _write_debug(self, method: str, kwargs: dict[str, Any], response: Any):
        payload = {"method": method, "kwargs": kwargs, "response": response}
        with self._output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str, sort_keys=True))
            handle.write("\n")


class DebuggableClient:
    def __init__(self, client: Any, output_path: str | Path):
        self._client = client
        self._output_path = Path(output_path)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

    def __getattr__(self, name: str):
        attr = getattr(self._client, name)
        if not callable(attr):
            return attr

        def wrapped(*args, **kwargs):
            result = attr(*args, **kwargs)
            if name == "get_paginator":
                method_name = args[0] if args else kwargs.get("method")
                return DebuggablePaginator(result, self._output_path, method_name)
            self._write_debug(name, kwargs, result)
            return result

        return wrapped

    def _write_debug(self, method: str, kwargs: dict[str, Any], response: Any):
        payload = {"method": method, "kwargs": kwargs, "response": response}
        with self._output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str, sort_keys=True))
            handle.write("\n")


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


def _result_key_candidates(result_key: str) -> list[str]:
    aliases = {
        "HoursList": ["HoursOfOperationSummaryList", "HoursList"],
        "ContactFlowModuleSummaryList": ["ContactFlowModulesSummaryList", "ContactFlowModuleSummaryList"],
    }
    return aliases.get(result_key, [result_key])


def _extract_list_values(payload: dict[str, Any], result_key: str) -> list[Any]:
    for candidate in _result_key_candidates(result_key):
        values = payload.get(candidate)
        if values is not None:
            if isinstance(values, list):
                return values
            return [values]
    return []


def list_all(client: Any, method: str, result_key: str, **kwargs) -> list[Any]:
    method_fn = getattr(client, method)
    try:
        if hasattr(client, "get_paginator"):
            paginator = client.get_paginator(method)
            pages = paginator.paginate(**kwargs)
            items: list[Any] = []
            for page in pages:
                items.extend(_extract_list_values(page, result_key))
            return items
        response = method_fn(**kwargs)
        return _extract_list_values(response, result_key)
    except Exception as exc:
        if _is_resource_not_found(exc):
            logger.warning("Skipping unreadable AWS Connect page for %s: %s", method, exc)
            return []
        raise
