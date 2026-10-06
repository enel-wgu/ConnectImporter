from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResourceType(str, Enum):
    INSTANCE = "instance"
    HOURS_OF_OPERATION = "hours_of_operation"
    QUEUE = "queue"
    ROUTING_PROFILE = "routing_profile"
    SECURITY_PROFILE = "security_profile"
    HIERARCHY_GROUP = "hierarchy_group"
    USER = "user"
    QUICK_CONNECT = "quick_connect"
    CONTACT_FLOW = "contact_flow"
    CONTACT_FLOW_MODULE = "contact_flow_module"
    PROMPT = "prompt"


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class IdentitySourceKind(str, Enum):
    CONNECT_MANAGED = "CONNECT_MANAGED"
    SAML = "SAML"
    EXISTING_DIRECTORY = "EXISTING_DIRECTORY"


@dataclass
class SourceMetadata:
    source_id: str | None = None


@dataclass
class ResourceReference:
    resource_type: ResourceType
    logical_name: str
    source_id: str = ""
    category: str = ""


@dataclass
class ExternalReference:
    key: str
    category: str
    value: str
    variable_name: str | None = None


@dataclass
class UnresolvedReference:
    resource_type: ResourceType
    source_id: str
    found_in_resource_type: ResourceType
    found_in_logical_name: str
    json_path: str


@dataclass
class ValidationIssue:
    severity: str
    resource_type: str
    logical_name: str
    source_id: str | None = None
    artifact: str = ""
    json_path: str = ""
    message: str = ""
    suggestion: str = ""

    def __str__(self) -> str:
        return f"{self.severity}:{self.resource_type}:{self.logical_name}:{self.message}"
