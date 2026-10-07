from __future__ import annotations

from connect_config.models.common import ValidationIssue
from connect_config.models.config_bundle import CanonicalConfig


def validate_config(config: CanonicalConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    resource_groups = {
        "hours_of_operation": config.hours_of_operation,
        "queue": config.queues,
        "routing_profile": config.routing_profiles,
        "security_profile": config.security_profiles,
        "hierarchy_group": config.hierarchy_groups,
        "user": config.users,
        "quick_connect": config.quick_connects,
        "contact_flow": config.contact_flows,
        "contact_flow_module": config.contact_flow_modules,
        "prompt": config.prompts,
    }
    queue_names = {queue.logical_name for queue in config.queues if getattr(queue, "logical_name", None)}
    for resource_type, items in resource_groups.items():
        seen: dict[str, str] = {}
        for item in items:
            logical_name = getattr(item, "logical_name", None)
            if logical_name:
                if logical_name in seen:
                    issues.append(ValidationIssue("ERROR", resource_type, logical_name, getattr(item, "source_id", None), resource_type, "", "Duplicate logical name detected.", "Use a unique logical name."))
                else:
                    seen[logical_name] = getattr(item, "source_id", None)

    for profile in config.routing_profiles:
        if profile.default_outbound_queue_ref and profile.default_outbound_queue_ref not in queue_names:
            issues.append(ValidationIssue("ERROR", "queue", profile.logical_name, profile.source_id, "routing_profile", "default_outbound_queue_ref", "Routing profile references a queue that is not present in the exported config.", "Ensure the queue exists and was exported with the same logical name."))
        for queue_config in getattr(profile, "queue_configs", []) or []:
            queue_ref = queue_config.get("queue_ref")
            if queue_ref and queue_ref not in queue_names:
                issues.append(ValidationIssue("ERROR", "queue", profile.logical_name, profile.source_id, "routing_profile", "queue_configs", "Routing profile queue config references a queue that is not present in the exported config.", "Resolve the queue reference or export the missing queue."))

    for quick_connect in config.quick_connects:
        if quick_connect.queue_ref and quick_connect.queue_ref not in queue_names:
            issues.append(ValidationIssue("ERROR", "queue", quick_connect.logical_name, quick_connect.source_id, "quick_connect", "queue_ref", "Quick connect references a queue that is not present in the exported config.", "Resolve the queue reference or export the missing queue."))

    for flow in config.contact_flows:
        for ref in flow.unresolved_references:
            issues.append(ValidationIssue("ERROR", "contact_flow", flow.logical_name, flow.source_id, "contact_flow", ref.get("json_path", ""), "Unresolved reference in contact flow.", "Resolve the reference or confirm the target instance contains the same resource."))
        for key in flow.unclassified_keys:
            issues.append(ValidationIssue("WARNING", "contact_flow", flow.logical_name, flow.source_id, "contact_flow", key, "Unclassified key found in flow content.", "Review the key manually."))
        for external in flow.external_references:
            issues.append(ValidationIssue("WARNING", "contact_flow", flow.logical_name, flow.source_id, "contact_flow", external.get("key", ""), "External dependency detected in contact flow.", "Review before deployment."))

    for module in config.contact_flow_modules:
        for ref in module.unresolved_references:
            issues.append(ValidationIssue("ERROR", "contact_flow_module", module.logical_name, module.source_id, "contact_flow_module", ref.get("json_path", ""), "Unresolved reference in flow module.", "Resolve the reference or confirm the target instance contains the same resource."))
        for key in module.unclassified_keys:
            issues.append(ValidationIssue("WARNING", "contact_flow_module", module.logical_name, module.source_id, "contact_flow_module", key, "Unclassified key found in flow module.", "Review the key manually."))
        for external in module.external_references:
            issues.append(ValidationIssue("WARNING", "contact_flow_module", module.logical_name, module.source_id, "contact_flow_module", external.get("key", ""), "External dependency detected in flow module.", "Review before deployment."))

    for user in config.users:
        if user.identity_source == "SAML" and user.identity.email:
            issues.append(ValidationIssue("WARNING", "user", user.logical_name, user.source_id, "user", "identity.email", "SAML identity management rejects email values for Connect users.", "Omit the email field under SAML-managed identity."))
        if user.identity_source == "EXISTING_DIRECTORY":
            issues.append(ValidationIssue("WARNING", "user", user.logical_name, user.source_id, "user", "identity", "Existing-directory user requires a target-specific directory_user_id.", "Supply a directory_user_id variable in tfvars before apply."))
        if not user.security_profile_refs:
            issues.append(ValidationIssue("ERROR", "user", user.logical_name, user.source_id, "user", "security_profile_refs", "User must reference at least one security profile.", "Attach a valid security profile."))

    for quick_connect in config.quick_connects:
        if quick_connect.quick_connect_type in {"QUEUE", "USER"} and not quick_connect.contact_flow_ref:
            issues.append(ValidationIssue("ERROR", "quick_connect", quick_connect.logical_name, quick_connect.source_id, "quick_connect", "contact_flow_ref", "Queue/user quick connect references an unresolved contact flow.", "Ensure the target flow exists and is registered."))
        if quick_connect.quick_connect_type == "PHONE_NUMBER":
            issues.append(ValidationIssue("WARNING", "quick_connect", quick_connect.logical_name, quick_connect.source_id, "quick_connect", "phone_number", "Phone-number quick connect is environment specific.", "Confirm the destination phone number before deployment."))

    return issues
