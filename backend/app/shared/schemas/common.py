from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiMeta(BaseModel):
    page: int = 1
    limit: int = 20
    total: int = 0
    totalPages: int | None = None
    cursor: str | None = None
    nextCursor: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: ApiMeta | None = None
    errors: list[dict[str, Any]] | None = None


class ListQuery(BaseModel):
    model_config = ConfigDict(extra="allow")

    q: str | None = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=200)
    sort: str = "-updatedAt"
    status: str | None = None
    stage: str | None = None
    startDate: str | None = None
    endDate: str | None = None


class PersonSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    email: str | None = None
    avatarUrl: str | None = None


class EntityComment(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    entityType: str
    entityId: str
    body: str
    author: PersonSummary | None = None
    createdAt: str
    editedAt: str | None = None
