from __future__ import annotations

from pydantic import BaseModel, Field

from .common import IdentitySourceKind


class UserIdentity(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    secondary_email: str | None = None
    mobile: str | None = None


class ConnectUserConfig(BaseModel):
    routing_profile_ref: str | None = None
    security_profile_refs: list[str] = Field(default_factory=list)
    hierarchy_group_ref: str | None = None


class User(BaseModel):
    logical_name: str
    source_id: str
    username: str | None = None
    name: str
    identity: UserIdentity = Field(default_factory=UserIdentity)
    identity_source: IdentitySourceKind = IdentitySourceKind.CONNECT_MANAGED
    routing_profile_ref: str | None = None
    security_profile_refs: list[str] = Field(default_factory=list)
    hierarchy_group_ref: str | None = None

    model_config = {"extra": "allow"}
