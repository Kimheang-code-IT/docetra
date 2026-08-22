from pydantic import BaseModel, ConfigDict, Field


class SettingEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    updatedAt: str | None = None
