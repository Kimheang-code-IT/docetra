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
