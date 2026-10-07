from __future__ import annotations

from dataclasses import dataclass, field

from connect_config.models.config_bundle import CanonicalConfig


@dataclass
class CollectedVariables:
    entries: dict[str, str] = field(default_factory=dict)


def collect_variables(config: CanonicalConfig) -> CollectedVariables:
    entries: dict[str, str] = {"connect_instance_id": "string"}
    for flow in list(config.contact_flows) + list(config.contact_flow_modules):
        for external in flow.external_references:
            if external.get("category", "").endswith("_preserved_verbatim"):
                continue
            variable_name = external.get("variable_name")
            if variable_name:
                entries[variable_name] = "string"
    for user in config.users:
        if user.identity_source == "EXISTING_DIRECTORY":
            entries[f"directory_user_id_{user.logical_name}"] = "string"
        if user.identity_source == "CONNECT_MANAGED":
            entries[f"user_password_{user.logical_name}"] = "string"
    return CollectedVariables(entries=entries)
