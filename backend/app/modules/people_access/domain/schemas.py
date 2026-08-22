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


class LoginResponse(BaseModel):
    user: AuthUser

class UserPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    name: str | None = None
    email: str | None = None
    roleId: str | None = None
    roleName: str | None = None
    officerId: str | None = None
    status: str | None = None
    permissions: list[str] = Field(default_factory=list)


class RolePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    permissions: list[str] = Field(default_factory=list)
    permissionRows: list[dict] = Field(default_factory=list)
