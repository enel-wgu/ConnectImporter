from __future__ import annotations

import json
from typing import Any

from connect_config.generation.terraform.attributes import resource_address
from connect_config.generation.terraform.hcl import resource, string_list
from connect_config.generation.terraform.variables import collect_variables
from connect_config.models.config_bundle import CanonicalConfig


def _resource_list(items: list[str]) -> str:
    refs = [resource_address("quick_connect", item) for item in items if item]
    return "[" + ", ".join(refs) + "]" if refs else "[]"


def _template_args(flow: Any) -> dict[str, str]:
    args: dict[str, str] = {}
    for var_name, reference in flow.template_variables.items():
        args[var_name] = resource_address(reference.resource_type, reference.logical_name)
    for external in flow.external_references:
        if external.get("category", "").endswith("_preserved_verbatim"):
            continue
        variable_name = external.get("variable_name")
        if variable_name:
            args[variable_name] = f"var.{variable_name}"
    return args


def render_hours_of_operation(item: Any) -> str:
    return resource("hours", "aws_connect_hours_of_operation", [
        '  instance_id = var.connect_instance_id',
        f'  name        = "{item.name}"',
    ])


def render_queue(item: Any) -> str:
    return resource(item.logical_name, "aws_connect_queue", [
        '  instance_id = var.connect_instance_id',
        f'  name = "{item.name}"',
        f'  description = "{item.description or ""}"',
        f'  hours_of_operation_id = {resource_address("hours_of_operation", item.hours_of_operation_ref or "") if item.hours_of_operation_ref else "null"}',
        f'  quick_connect_ids = {_resource_list(item.quick_connect_refs)}',
    ])


def render_routing_profile(item: Any) -> str:
    lines = [
        '  instance_id = var.connect_instance_id',
        f'  name = "{item.name}"',
        f'  default_outbound_queue_id = {resource_address("queue", item.default_outbound_queue_ref or "") if item.default_outbound_queue_ref else "null"}',
    ]
    for queue_config in getattr(item, "queue_configs", []) or []:
        queue_ref = queue_config.get("queue_ref")
        if not queue_ref:
            continue
        lines.append('  queue_config {')
        lines.append(f'    channel = {json.dumps(queue_config.get("channel") or "VOICE")}')
        lines.append(f'    delay = {queue_config.get("delay", 0)}')
        lines.append(f'    priority = {queue_config.get("priority", 1)}')
        lines.append('    queue_reference {')
        lines.append(f'      channel = {json.dumps(queue_config.get("channel") or "VOICE")}')
        lines.append(f'      queue_id = {resource_address("queue", queue_ref)}')
        lines.append('    }')
        lines.append('  }')
    return resource(item.logical_name, "aws_connect_routing_profile", lines)


def render_security_profile(item: Any) -> str:
    return resource(item.logical_name, "aws_connect_security_profile", [
        '  instance_id = var.connect_instance_id',
        f'  name = "{item.name}"',
        f'  permissions = {string_list(item.permissions)}',
    ])


def render_hierarchy_group(item: Any) -> str:
    return resource(item.logical_name, "aws_connect_user_hierarchy_group", [
        '  instance_id = var.connect_instance_id',
        f'  name = "{item.name}"',
        f'  parent_group_id = {resource_address("hierarchy_group", item.parent_group_ref or "") if item.parent_group_ref else "null"}',
    ])


def render_user(item: Any) -> str:
    lines = [
        '  instance_id = var.connect_instance_id',
        f'  username = "{item.username or item.name}"',
        f'  name = "{item.name}"',
    ]
    if item.identity_source == "SAML":
        lines.append('  # SAML identity management rejects email values; the target IdP handles them externally.')
    elif item.identity_source == "CONNECT_MANAGED":
        lines.append(f'  password = var.user_password_{item.logical_name}')
    elif item.identity_source == "EXISTING_DIRECTORY":
        lines.append(f'  directory_user_id = var.directory_user_id_{item.logical_name}')
    if item.routing_profile_ref:
        lines.append(f'  routing_profile_id = {resource_address("routing_profile", item.routing_profile_ref)}')
    if item.security_profile_refs:
        lines.append(f'  security_profile_ids = {string_list(item.security_profile_refs)}')
    if item.hierarchy_group_ref:
        lines.append(f'  hierarchy_group_id = {resource_address("hierarchy_group", item.hierarchy_group_ref)}')
    return resource(item.logical_name, "aws_connect_user", lines)


def render_quick_connect(item: Any) -> str:
    body = [
        '  instance_id = var.connect_instance_id',
        f'  name = "{item.name}"',
    ]
    if item.quick_connect_type == "QUEUE":
        body.append('  quick_connect_config {')
        body.append('    quick_connect_type = "QUEUE"')
        body.append('    queue_config {')
        body.append(f'      queue_id = {resource_address("queue", item.queue_ref or "") if item.queue_ref else "null"}')
        body.append(f'      contact_flow_id = {resource_address("contact_flow", item.contact_flow_ref or "") if item.contact_flow_ref else "null"}')
        body.append('    }')
        body.append('  }')
    elif item.quick_connect_type == "USER":
        body.append('  quick_connect_config {')
        body.append('    quick_connect_type = "USER"')
        body.append('    user_config {')
        body.append(f'      user_id = {resource_address("user", item.user_ref or "") if item.user_ref else "null"}')
        body.append(f'      contact_flow_id = {resource_address("contact_flow", item.contact_flow_ref or "") if item.contact_flow_ref else "null"}')
        body.append('    }')
        body.append('  }')
    else:
        body.append('  quick_connect_config {')
        body.append('    quick_connect_type = "PHONE_NUMBER"')
        body.append(f'    phone_config {{ phone_number = {json.dumps(item.phone_number or "")} }}')
        body.append('  }')
    return resource(item.logical_name, "aws_connect_quick_connect", body)


def render_prompt(item: Any) -> str:
    return resource(item.logical_name, "aws_connect_prompt", [
        '  instance_id = var.connect_instance_id',
        f'  name = "{item.name}"',
    ])


def render_contact_flow(item: Any) -> str:
    args = _template_args(item)
    body = [
        '  instance_id = var.connect_instance_id',
        f'  name = "{item.name}"',
        '  type = "CONTACT_FLOW"',
        f'  content = templatefile("${{path.module}}/flows/{item.logical_name}.json.tftpl", {json.dumps(args, indent=2, sort_keys=True)})',
    ]
    return resource(item.logical_name, "aws_connect_contact_flow", body)


def render_contact_flow_module(item: Any) -> str:
    args = _template_args(item)
    body = [
        '  instance_id = var.connect_instance_id',
        f'  name = "{item.name}"',
        f'  content = templatefile("${{path.module}}/flows/{item.logical_name}.json.tftpl", {json.dumps(args, indent=2, sort_keys=True)})',
    ]
    return resource(item.logical_name, "aws_connect_contact_flow_module", body)


def render_variables(config: CanonicalConfig) -> str:
    collected = collect_variables(config)
    lines = []
    for name, variable_type in collected.entries.items():
        lines.append('variable "' + name + '" {')
        lines.append(f'  type = "{variable_type}"')
        lines.append('}')
        lines.append('')
    return '\n'.join(lines)


def generate_terraform(config: CanonicalConfig) -> dict[str, str]:
    files: dict[str, str] = {"variables.tf": render_variables(config)}
    for name in collect_variables(config).entries:
        if "lambda" in name or "lex" in name or "phone" in name or "directory_user_id" in name or "user_password" in name:
            files[f"{name}.tf"] = f'variable "{name}" {{\n  type = "string"\n}}\n'
    for item in config.hours_of_operation:
        files[f"hours_of_operation_{item.logical_name}.tf"] = render_hours_of_operation(item)
    for item in config.queues:
        files[f"queue_{item.logical_name}.tf"] = render_queue(item)
    for item in config.routing_profiles:
        files[f"routing_profile_{item.logical_name}.tf"] = render_routing_profile(item)
    for item in config.security_profiles:
        files[f"security_profile_{item.logical_name}.tf"] = render_security_profile(item)
    for item in config.hierarchy_groups:
        files[f"hierarchy_group_{item.logical_name}.tf"] = render_hierarchy_group(item)
    for item in config.users:
        files[f"user_{item.logical_name}.tf"] = render_user(item)
    for item in config.quick_connects:
        files[f"quick_connect_{item.logical_name}.tf"] = render_quick_connect(item)
    for item in config.prompts:
        files[f"prompt_{item.logical_name}.tf"] = render_prompt(item)
    for item in config.contact_flows:
        files[f"contact_flow_{item.logical_name}.tf"] = render_contact_flow(item)
    for item in config.contact_flow_modules:
        files[f"contact_flow_module_{item.logical_name}.tf"] = render_contact_flow_module(item)
    return files
