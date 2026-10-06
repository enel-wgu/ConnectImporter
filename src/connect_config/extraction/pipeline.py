from __future__ import annotations

from connect_config.extraction.base import ExtractionContext, NormalizationContext
from connect_config.extraction.registry import ORDERED_HANDLERS
from connect_config.models.config_bundle import CanonicalConfig


def run_export(client, instance_id: str) -> CanonicalConfig:
    catalog = __import__("connect_config.references.catalog", fromlist=["ReferenceCatalog"]).ReferenceCatalog()
    ctx = ExtractionContext(client=client, instance_id=instance_id)
    extracted: dict[str, list[dict]] = {}
    for handler in ORDERED_HANDLERS:
        extracted[handler.resource_type] = handler.extract(ctx)

    preassigned = {"contact_flow": {}, "contact_flow_module": {}}
    for raw in extracted.get("contact_flow_module", []):
        flow_id = raw.get("ContactFlowModuleId") or raw.get("Id")
        if flow_id:
            name = raw.get("Name", flow_id)
            preassigned["contact_flow_module"][flow_id] = name.lower().replace(" ", "_")
    for raw in extracted.get("contact_flow", []):
        flow_id = raw.get("ContactFlowId") or raw.get("Id")
        if flow_id:
            name = raw.get("Name", flow_id)
            preassigned["contact_flow"][flow_id] = name.lower().replace(" ", "_")

    normalizer = NormalizationContext(catalog=catalog, client=client, instance_id=instance_id, preassigned_names=preassigned)
    normalized: dict[str, list] = {}
    for handler in ORDERED_HANDLERS:
        normalized[handler.resource_type] = handler.normalize(extracted.get(handler.resource_type, []), normalizer)

    queue_handler = next((h for h in ORDERED_HANDLERS if h.resource_type == "queue"), None)
    quick_connect_handler = next((h for h in ORDERED_HANDLERS if h.resource_type == "quick_connect"), None)
    if queue_handler and hasattr(queue_handler, "backfill_quick_connects"):
        queue_handler.backfill_quick_connects(normalized.get("queue", []), catalog)
    if quick_connect_handler and hasattr(quick_connect_handler, "backfill_contact_flow_refs"):
        quick_connect_handler.backfill_contact_flow_refs(normalized.get("quick_connect", []), catalog)

    config = CanonicalConfig(
        instance=normalized.get("instance", []),
        hours_of_operation=normalized.get("hours_of_operation", []),
        queues=normalized.get("queue", []),
        routing_profiles=normalized.get("routing_profile", []),
        security_profiles=normalized.get("security_profile", []),
        hierarchy_groups=normalized.get("hierarchy_group", []),
        users=normalized.get("user", []),
        quick_connects=normalized.get("quick_connect", []),
        contact_flows=normalized.get("contact_flow", []),
        contact_flow_modules=normalized.get("contact_flow_module", []),
        prompts=normalized.get("prompt", []),
        skipped_flows=[item for handler in ORDERED_HANDLERS if hasattr(handler, "skipped") for item in getattr(handler, "skipped", [])],
    )
    return config
