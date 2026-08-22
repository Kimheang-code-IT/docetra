from pydantic import BaseModel, ConfigDict, Field


class SearchHit(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str | None = None
    entityType: str | None = None
    url: str | None = None


class AskRequest(BaseModel):
    q: str = ""

class ExportCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    resource: str
    format: str | None = "csv"
    scope: str | None = None
    selectedIds: list[str] = Field(default_factory=list)
    fieldCodes: list[str] = Field(default_factory=list)
