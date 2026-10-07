from __future__ import annotations

import copy
import json
from typing import Any

from connect_config.models.common import ResourceType, ResourceReference, UnresolvedReference
from connect_config.references.catalog import ReferenceCatalog
from connect_config.references.classification import FLOW_PARAMETER_RULES, KNOWN_NON_REFERENCE_KEYS


def _var_name(category: str, logical_name: str) -> str:
    base = f"{category}_{logical_name}"
    base = base.replace("-", "_")
    base = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in base)
    base = base.strip("_")
    return base[:48]


def resolve_flow_content(content: dict[str, Any], catalog: ReferenceCatalog, resource_type: ResourceType, logical_name: str, source_id: str) -> dict[str, Any]:
    resolved = copy.deepcopy(content)
    template_variables: dict[str, ResourceReference] = {}
    external_references: list[dict[str, Any]] = []
    unresolved_references: list[dict[str, Any]] = []
    unclassified_keys: list[str] = []

    if not isinstance(resolved, dict):
        return {
            "resolved_json": resolved,
            "template_variables": template_variables,
            "external_references": external_references,
            "unresolved_references": unresolved_references,
            "unclassified_keys": unclassified_keys,
            "is_valid": False,
        }

    actions = resolved.get("Actions", [])
    if not isinstance(actions, list):
        actions = []

    for action_index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        parameters = action.get("Parameters", {})
        if not isinstance(parameters, dict):
            continue
        for key, value in list(parameters.items()):
            rule = FLOW_PARAMETER_RULES.get(key)
            if rule is None:
                if key not in KNOWN_NON_REFERENCE_KEYS and (key.endswith("Id") or key.endswith("Arn") or key.endswith("ARN")):
                    unclassified_keys.append(f"Actions[{action_index}].Parameters.{key}")
                continue
            if rule.kind == "TRANSLATED":
                if not isinstance(value, str):
                    continue
                resolved_name = catalog.resolve(rule.resource_type.value if isinstance(rule.resource_type, ResourceType) else str(rule.resource_type), value)
                if resolved_name:
                    var_name = _var_name(rule.category, resolved_name)
                    parameters[key] = f"${{{var_name}}}"
                else:
                    unresolved_references.append({
                        "resource_type": rule.resource_type.value if isinstance(rule.resource_type, ResourceType) else str(rule.resource_type),
                        "source_id": value,
                        "found_in_resource_type": resource_type.value,
                        "found_in_logical_name": logical_name,
                        "json_path": f"Actions[{action_index}].Parameters.{key}",
                    })
            elif rule.kind == "EXTERNAL_DEPENDENCY":
                var_name = _var_name(rule.category, logical_name)
                if isinstance(value, dict):
                    external_references.append({"key": key, "category": f"{rule.category}_preserved_verbatim", "value": json.dumps(value), "variable_name": var_name})
                    continue
                external_references.append({"key": key, "category": rule.category, "value": str(value), "variable_name": var_name})
                parameters[key] = f"${{{var_name}}}"
            elif rule.kind == "ENVIRONMENT_SPECIFIC":
                var_name = _var_name(rule.category, logical_name)
                external_references.append({"key": key, "category": rule.category, "value": str(value), "variable_name": var_name})
                parameters[key] = f"${{{var_name}}}"

    resolved["Actions"] = actions
    if "Metadata" in resolved:
        resolved.pop("Metadata", None)

    result = {
        "resolved_json": resolved,
        "template_variables": template_variables,
        "external_references": external_references,
        "unresolved_references": unresolved_references,
        "unclassified_keys": unclassified_keys,
        "is_valid": not unresolved_references,
    }
    return result
