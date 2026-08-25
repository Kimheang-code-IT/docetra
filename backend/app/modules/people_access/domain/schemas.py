from pydantic import BaseModel, ConfigDict, Field


class AuthUser(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | int | None = None
    name: str
    email: str
    role: str | None = None
    avatar: str | None = None
    permissions: list[str] = Field(default_factory=list)
    pageAccess: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    email: str
    password: str
