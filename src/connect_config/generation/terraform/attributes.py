from __future__ import annotations

from connect_config.models.common import ResourceType

TF_RESOURCE: dict[ResourceType, tuple[str, str]] = {
    ResourceType.HOURS_OF_OPERATION: ("aws_connect_hours_of_operation", "hours_of_operation_id"),
    ResourceType.QUEUE: ("aws_connect_queue", "queue_id"),
    ResourceType.ROUTING_PROFILE: ("aws_connect_routing_profile", "routing_profile_id"),
    ResourceType.SECURITY_PROFILE: ("aws_connect_security_profile", "security_profile_id"),
    ResourceType.HIERARCHY_GROUP: ("aws_connect_user_hierarchy_group", "hierarchy_group_id"),
    ResourceType.USER: ("aws_connect_user", "user_id"),
    ResourceType.QUICK_CONNECT: ("aws_connect_quick_connect", "quick_connect_id"),
    ResourceType.CONTACT_FLOW: ("aws_connect_contact_flow", "contact_flow_id"),
    ResourceType.CONTACT_FLOW_MODULE: ("aws_connect_contact_flow_module", "contact_flow_module_id"),
    ResourceType.PROMPT: ("data.aws_connect_prompt", "prompt_id"),
}


def resource_address(resource_type: ResourceType | str, logical_name: str) -> str:
    key = resource_type if isinstance(resource_type, ResourceType) else ResourceType(resource_type)
    if key == ResourceType.PROMPT:
        return "data.aws_connect_prompt.prompt_id"
    tf_resource, id_attr = TF_RESOURCE[key]
    return f"{tf_resource}.{logical_name}.{id_attr}"
