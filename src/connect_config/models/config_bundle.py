from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .common import ResourceReference
from .users import User


class InstanceConfig(BaseModel):
    logical_name: str
    source_id: str
    name: str
    instance_id: str | None = None


class HoursOfOperation(BaseModel):
    logical_name: str
    source_id: str
    name: str
    time_zone: str | None = None
    config: list[dict[str, Any]] = Field(default_factory=list)


class Queue(BaseModel):
    logical_name: str
    source_id: str
    name: str
    description: str | None = None
    hours_of_operation_ref: str | None = None
    quick_connect_refs: list[str] = Field(default_factory=list)
    status: str | None = None


class RoutingProfile(BaseModel):
    logical_name: str
    source_id: str
    name: str
    default_outbound_queue_ref: str | None = None
    queue_configs: list[dict[str, Any]] = Field(default_factory=list)


class SecurityProfile(BaseModel):
    logical_name: str
    source_id: str
    name: str
    permissions: list[str] = Field(default_factory=list)


class HierarchyGroup(BaseModel):
    logical_name: str
    source_id: str
    name: str
    parent_group_ref: str | None = None


class QuickConnect(BaseModel):
    logical_name: str
    source_id: str
    name: str
    quick_connect_type: str | None = None
    queue_ref: str | None = None
    user_ref: str | None = None
    contact_flow_ref: str | None = None
    phone_number: str | None = None


class ContactFlow(BaseModel):
    logical_name: str
    source_id: str
    name: str
    content: dict[str, Any] | None = None
    resolved_json: dict[str, Any] | None = None
    template_variables: dict[str, ResourceReference] = Field(default_factory=dict)
    external_references: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_references: list[dict[str, Any]] = Field(default_factory=list)
    unclassified_keys: list[str] = Field(default_factory=list)
    is_valid: bool = True


class ContactFlowModule(BaseModel):
    logical_name: str
    source_id: str
    name: str
    content: dict[str, Any] | None = None
    resolved_json: dict[str, Any] | None = None
    template_variables: dict[str, ResourceReference] = Field(default_factory=dict)
    external_references: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_references: list[dict[str, Any]] = Field(default_factory=list)
    unclassified_keys: list[str] = Field(default_factory=list)
    is_valid: bool = True


class Prompt(BaseModel):
    logical_name: str
    source_id: str
    name: str
    description: str | None = None


class CanonicalConfig(BaseModel):
    instance: list[InstanceConfig] = Field(default_factory=list)
    hours_of_operation: list[HoursOfOperation] = Field(default_factory=list)
    queues: list[Queue] = Field(default_factory=list)
    routing_profiles: list[RoutingProfile] = Field(default_factory=list)
    security_profiles: list[SecurityProfile] = Field(default_factory=list)
    hierarchy_groups: list[HierarchyGroup] = Field(default_factory=list)
    users: list[User] = Field(default_factory=list)
    quick_connects: list[QuickConnect] = Field(default_factory=list)
    contact_flows: list[ContactFlow] = Field(default_factory=list)
    contact_flow_modules: list[ContactFlowModule] = Field(default_factory=list)
    prompts: list[Prompt] = Field(default_factory=list)
    skipped_flows: list[str] = Field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "Queues": len(self.queues),
            "Routing profiles": len(self.routing_profiles),
            "Security profiles": len(self.security_profiles),
            "Users": len(self.users),
            "Hierarchy groups": len(self.hierarchy_groups),
            "Hours": len(self.hours_of_operation),
            "Contact flows": len(self.contact_flows),
            "Flow modules": len(self.contact_flow_modules),
            "Prompts": len(self.prompts),
            "Quick connects": len(self.quick_connects),
        }
