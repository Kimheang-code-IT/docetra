from pydantic import BaseModel, ConfigDict


class StorageProviderPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    name: str | None = None
    provider: str | None = None
    active: bool | None = None
    isDefault: bool | None = None
