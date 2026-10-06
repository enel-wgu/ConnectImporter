from __future__ import annotations

import json

from connect_config.models.config_bundle import CanonicalConfig


def generate_flow_artifacts(config: CanonicalConfig) -> dict[str, str]:
    files: dict[str, str] = {}
    for flow in config.contact_flows:
        files[f"flows/{flow.logical_name}.json.tftpl"] = json.dumps(flow.resolved_json or {}, indent=2, sort_keys=True)
    for flow in config.contact_flow_modules:
        files[f"flow_modules/{flow.logical_name}.json.tftpl"] = json.dumps(flow.resolved_json or {}, indent=2, sort_keys=True)
    return files
