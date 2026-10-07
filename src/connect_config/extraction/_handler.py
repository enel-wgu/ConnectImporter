from __future__ import annotations

from typing import Any

from connect_config.aws.client import list_all
from connect_config.models.common import ResourceType
from connect_config.models.config_bundle import (
    ContactFlow,
    ContactFlowModule,
    HierarchyGroup,
    HoursOfOperation,
    InstanceConfig,
    Prompt,
    Queue,
    QuickConnect,
    RoutingProfile,
    SecurityProfile,
    User,
)
from connect_config.models.users import UserIdentity
from connect_config.normalization.naming import LogicalNameAllocator
from connect_config.references.flow_resolver import resolve_flow_content


class InstanceHandler:
    resource_type = "instance"

    def extract(self, ctx):
        summaries = list_all(ctx.client, "list_instances", "InstanceSummaryList")
        return summaries if summaries else [{"Id": ctx.instance_id, "Arn": f"arn:aws:connect:{ctx.instance_id}"}]

    def normalize(self, raw, ctx):
        rows = []
        for item in raw:
            instance_id = item.get("Id") or item.get("InstanceId") or ctx.instance_id
            rows.append(InstanceConfig(logical_name="main", source_id=instance_id, name=item.get("Name") or "Instance", instance_id=instance_id))
        return rows


class HoursHandler:
    resource_type = "hours_of_operation"

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_hours_of_operations", "HoursList", InstanceId=ctx.instance_id):
            hours_id = summary.get("HoursOfOperationId") or summary.get("Id")
            detail = ctx.client.describe_hours_of_operation(InstanceId=ctx.instance_id, HoursOfOperationId=hours_id)
            rows.append(detail.get("HoursOfOperation", summary))
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("hours_of_operation")
        rows = []
        for item in raw:
            source_id = item.get("HoursOfOperationId") or item.get("Id")
            logical_name = allocator.allocate(item.get("Name", source_id))
            ctx.catalog.register("hours_of_operation", source_id, logical_name)
            rows.append(HoursOfOperation(logical_name=logical_name, source_id=source_id, name=item.get("Name", source_id), time_zone=item.get("TimeZone"), config=item.get("Config", [])))
        return rows


class QueuesHandler:
    resource_type = "queue"

    def __init__(self):
        self._raw_quick_connect_ids: dict[str, list[str]] = {}

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_queues", "QueueSummaryList", InstanceId=ctx.instance_id):
            queue_id = summary.get("Id") or summary.get("QueueId")
            if not queue_id:
                continue
            try:
                detail = ctx.client.describe_queue(InstanceId=ctx.instance_id, QueueId=queue_id)
            except Exception as exc:  # pragma: no cover - defensive AWS API handling
                if "Queue not found" in str(exc) or "ResourceNotFoundException" in str(exc):
                    continue
                raise
            rows.append(detail.get("Queue", summary))
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("queue")
        rows = []
        for item in raw:
            source_id = item.get("QueueId") or item.get("Id")
            logical_name = allocator.allocate(item.get("Name", source_id))
            ctx.catalog.register("queue", source_id, logical_name)
            hours_of_operation_ref = ctx.catalog.resolve("hours_of_operation", item.get("HoursOfOperationId"))
            quick_connect_ids = list_all(ctx.client, "list_queue_quick_connects", "QuickConnectSummaryList", InstanceId=ctx.instance_id, QueueId=source_id)
            self._raw_quick_connect_ids[source_id] = [item.get("Id") or item.get("QuickConnectId") for item in quick_connect_ids]
            rows.append(Queue(logical_name=logical_name, source_id=source_id, name=item.get("Name", source_id), description=item.get("Description"), hours_of_operation_ref=hours_of_operation_ref, quick_connect_refs=[], status=item.get("Status")))
        return rows

    def backfill_quick_connects(self, queues, catalog):
        for queue in queues:
            refs = []
            for quick_connect_id in self._raw_quick_connect_ids.get(queue.source_id, []):
                resolved = catalog.resolve("quick_connect", quick_connect_id)
                if resolved:
                    refs.append(resolved)
            queue.quick_connect_refs = refs


class RoutingProfilesHandler:
    resource_type = "routing_profile"

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_routing_profiles", "RoutingProfileSummaryList", InstanceId=ctx.instance_id):
            profile_id = summary.get("Id") or summary.get("RoutingProfileId")
            if not profile_id:
                continue
            try:
                detail = ctx.client.describe_routing_profile(InstanceId=ctx.instance_id, RoutingProfileId=profile_id)
            except Exception as exc:  # pragma: no cover - defensive AWS API handling
                if "Routing profile not found" in str(exc) or "ResourceNotFoundException" in str(exc):
                    continue
                raise
            route = detail.get("RoutingProfile", summary)
            rows.append(route)
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("routing_profile")
        rows = []
        for item in raw:
            source_id = item.get("RoutingProfileId") or item.get("Id")
            logical_name = allocator.allocate(item.get("Name", source_id))
            ctx.catalog.register("routing_profile", source_id, logical_name)
            config = list_all(ctx.client, "list_routing_profile_queues", "QueueConfigSummaryList", InstanceId=ctx.instance_id, RoutingProfileId=source_id)
            queue_refs = []
            for entry in config:
                queue_id = entry.get("QueueId")
                if queue_id:
                    queue_refs.append({"channel": entry.get("Channel"), "delay": entry.get("Delay"), "priority": entry.get("Priority"), "queue_ref": ctx.catalog.resolve("queue", queue_id)})
            rows.append(RoutingProfile(logical_name=logical_name, source_id=source_id, name=item.get("Name", source_id), default_outbound_queue_ref=ctx.catalog.resolve("queue", item.get("DefaultOutboundQueueId")), queue_configs=queue_refs))
        return rows


class SecurityProfilesHandler:
    resource_type = "security_profile"

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_security_profiles", "SecurityProfileSummaryList", InstanceId=ctx.instance_id):
            profile_id = summary.get("Id") or summary.get("SecurityProfileId")
            detail = ctx.client.describe_security_profile(InstanceId=ctx.instance_id, SecurityProfileId=profile_id)
            row = detail.get("SecurityProfile", summary)
            perms = list_all(ctx.client, "list_security_profile_permissions", "Permissions", InstanceId=ctx.instance_id, SecurityProfileId=profile_id)
            row["Permissions"] = perms
            rows.append(row)
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("security_profile")
        rows = []
        for item in raw:
            source_id = item.get("SecurityProfileId") or item.get("Id")
            logical_name = allocator.allocate(item.get("Name", source_id))
            ctx.catalog.register("security_profile", source_id, logical_name)
            rows.append(SecurityProfile(logical_name=logical_name, source_id=source_id, name=item.get("Name", source_id), permissions=item.get("Permissions", [])))
        return rows


class HierarchyHandler:
    resource_type = "hierarchy_group"

    def extract(self, ctx):
        rows = []
        structure = ctx.client.describe_user_hierarchy_structure(InstanceId=ctx.instance_id)
        groups = list_all(ctx.client, "list_user_hierarchy_groups", "HierarchyGroupSummaryList", InstanceId=ctx.instance_id)
        for summary in groups:
            group_id = summary.get("Id") or summary.get("HierarchyGroupId")
            detail = ctx.client.describe_user_hierarchy_group(InstanceId=ctx.instance_id, HierarchyGroupId=group_id)
            row = detail.get("HierarchyGroup", summary)
            rows.append(row)
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("hierarchy_group")
        rows = []
        for item in raw:
            source_id = item.get("HierarchyGroupId") or item.get("Id")
            logical_name = allocator.allocate(item.get("Name", source_id))
            ctx.catalog.register("hierarchy_group", source_id, logical_name)
            rows.append(HierarchyGroup(logical_name=logical_name, source_id=source_id, name=item.get("Name", source_id), parent_group_ref=ctx.catalog.resolve("hierarchy_group", item.get("ParentGroupId"))))
        return rows


class UserHandler:
    resource_type = "user"

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_users", "UserSummaryList", InstanceId=ctx.instance_id):
            user_id = summary.get("Id") or summary.get("UserId")
            detail = ctx.client.describe_user(InstanceId=ctx.instance_id, UserId=user_id)
            rows.append(detail.get("User", summary))
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("user")
        rows = []
        for item in raw:
            source_id = item.get("UserId") or item.get("Id")
            logical_name = allocator.allocate(item.get("Username") or item.get("IdentityInfo", {}).get("FirstName") or source_id)
            ctx.catalog.register("user", source_id, logical_name)
            identity_info = item.get("IdentityInfo", {})
            row = User(
                logical_name=logical_name,
                source_id=source_id,
                username=item.get("Username"),
                name=f"{identity_info.get('FirstName','')} {identity_info.get('LastName','')}".strip() or item.get("Username") or source_id,
                identity=UserIdentity(
                    first_name=identity_info.get("FirstName"),
                    last_name=identity_info.get("LastName"),
                    email=identity_info.get("Email"),
                    secondary_email=identity_info.get("SecondaryEmail"),
                    mobile=identity_info.get("Mobile"),
                ),
                identity_source=item.get("IdentityManagementType", "CONNECT_MANAGED"),
                routing_profile_ref=ctx.catalog.resolve("routing_profile", item.get("RoutingProfileId")),
                security_profile_refs=[ctx.catalog.resolve("security_profile", profile_id) for profile_id in item.get("SecurityProfileIds", []) if ctx.catalog.resolve("security_profile", profile_id)],
                hierarchy_group_ref=ctx.catalog.resolve("hierarchy_group", item.get("HierarchyGroupId")),
            )
            rows.append(row)
        return rows


class QuickConnectsHandler:
    resource_type = "quick_connect"

    def __init__(self):
        self._raw_queue_ids: dict[str, str] = {}
        self._raw_user_ids: dict[str, str] = {}
        self._raw_contact_flow_ids: dict[str, str] = {}

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_quick_connects", "QuickConnectSummaryList", InstanceId=ctx.instance_id):
            quick_connect_id = summary.get("Id") or summary.get("QuickConnectId")
            detail = ctx.client.describe_quick_connect(InstanceId=ctx.instance_id, QuickConnectId=quick_connect_id)
            rows.append(detail.get("QuickConnect", summary))
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("quick_connect")
        rows = []
        for item in raw:
            source_id = item.get("QuickConnectId") or item.get("Id")
            cfg = item.get("QuickConnectConfig", {})
            quick_connect_type = cfg.get("QuickConnectType", "QUEUE")
            logical_name = allocator.allocate(item.get("Name", source_id))
            ctx.catalog.register("quick_connect", source_id, logical_name)
            queue_config = cfg.get("QueueConfig", {})
            user_config = cfg.get("UserConfig", {})
            self._raw_queue_ids[source_id] = queue_config.get("QueueId") or ""
            self._raw_user_ids[source_id] = user_config.get("UserId") or ""
            self._raw_contact_flow_ids[source_id] = (queue_config.get("ContactFlowId") or user_config.get("ContactFlowId") or "")
            rows.append(QuickConnect(
                logical_name=logical_name,
                source_id=source_id,
                name=item.get("Name", source_id),
                quick_connect_type=quick_connect_type,
                queue_ref=ctx.catalog.resolve("queue", self._raw_queue_ids[source_id]),
                user_ref=ctx.catalog.resolve("user", self._raw_user_ids[source_id]),
                contact_flow_ref=None,
                phone_number=cfg.get("PhoneConfig", {}).get("PhoneNumber"),
            ))
        return rows

    def backfill_contact_flow_refs(self, quick_connects, catalog):
        for quick_connect in quick_connects:
            flow_id = self._raw_contact_flow_ids.get(quick_connect.source_id)
            if flow_id:
                quick_connect.contact_flow_ref = catalog.resolve("contact_flow", flow_id)


class PromptsHandler:
    resource_type = "prompt"

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_prompts", "PromptSummaryList", InstanceId=ctx.instance_id):
            prompt_id = summary.get("Id") or summary.get("PromptId")
            rows.append({"PromptId": prompt_id, "Name": summary.get("Name", prompt_id)})
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("prompt")
        rows = []
        for item in raw:
            source_id = item.get("PromptId") or item.get("Id")
            logical_name = allocator.allocate(item.get("Name", source_id))
            ctx.catalog.register("prompt", source_id, logical_name)
            rows.append(Prompt(logical_name=logical_name, source_id=source_id, name=item.get("Name", source_id), description=item.get("Description")))
        return rows


class ContactFlowModulesHandler:
    resource_type = "contact_flow_module"

    def __init__(self):
        self.skipped: list[str] = []

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_contact_flow_modules", "ContactFlowModuleSummaryList", InstanceId=ctx.instance_id):
            flow_module_id = summary.get("Id") or summary.get("ContactFlowModuleId")
            detail = ctx.client.describe_contact_flow_module(InstanceId=ctx.instance_id, ContactFlowModuleId=flow_module_id)
            rows.append(detail.get("ContactFlowModule", summary))
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("contact_flow_module")
        rows = []
        for item in raw:
            source_id = item.get("ContactFlowModuleId") or item.get("Id")
            logical_name = ctx.preassigned_names["contact_flow_module"].get(source_id) or allocator.allocate(item.get("Name", source_id))
            ctx.catalog.register("contact_flow_module", source_id, logical_name)
            content = item.get("Content", {})
            resolved = resolve_flow_content(content, ctx.catalog, ResourceType.CONTACT_FLOW_MODULE, logical_name, source_id)
            row = ContactFlowModule(logical_name=logical_name, source_id=source_id, name=item.get("Name", source_id), content=content, resolved_json=resolved["resolved_json"], template_variables=resolved["template_variables"], external_references=resolved["external_references"], unresolved_references=resolved["unresolved_references"], unclassified_keys=resolved["unclassified_keys"], is_valid=resolved["is_valid"])
            rows.append(row)
        return rows


class ContactFlowsHandler:
    resource_type = "contact_flow"

    def __init__(self):
        self.skipped: list[str] = []

    def extract(self, ctx):
        rows = []
        for summary in list_all(ctx.client, "list_contact_flows", "ContactFlowSummaryList", InstanceId=ctx.instance_id):
            flow_id = summary.get("Id") or summary.get("ContactFlowId")
            detail = ctx.client.describe_contact_flow(InstanceId=ctx.instance_id, ContactFlowId=flow_id)
            rows.append(detail.get("ContactFlow", summary))
        return rows

    def normalize(self, raw, ctx):
        allocator = LogicalNameAllocator("contact_flow")
        rows = []
        for item in raw:
            source_id = item.get("ContactFlowId") or item.get("Id")
            flow_name = item.get("Name", source_id)
            if flow_name == "Default customer queue":
                self.skipped.append(flow_name)
                continue
            logical_name = ctx.preassigned_names["contact_flow"].get(source_id) or allocator.allocate(flow_name)
            ctx.catalog.register("contact_flow", source_id, logical_name)
            content = item.get("Content", {})
            resolved = resolve_flow_content(content, ctx.catalog, ResourceType.CONTACT_FLOW, logical_name, source_id)
            row = ContactFlow(logical_name=logical_name, source_id=source_id, name=flow_name, content=content, resolved_json=resolved["resolved_json"], template_variables=resolved["template_variables"], external_references=resolved["external_references"], unresolved_references=resolved["unresolved_references"], unclassified_keys=resolved["unclassified_keys"], is_valid=resolved["is_valid"])
            rows.append(row)
        return rows
