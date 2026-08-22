from pydantic import BaseModel, ConfigDict, Field


class OrganizationPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    name: str | None = None
    code: str | None = None
    parentId: str | None = None
    organizationType: str | None = None
    status: str | None = None
    description: str | None = None


class OfficerPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    name: str | None = None
    email: str | None = None
    organizationId: str | None = None
    departmentId: str | None = None
    roleId: str | None = None
    status: str | None = None
