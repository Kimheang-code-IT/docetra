"""Shared HTTP envelopes and mutation payloads."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    data: Any = None
    meta: dict[str, Any] | None = None
    message: str | None = None


class MutationBody(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: int | None = None


class CommentBody(BaseModel):
    body: str = Field(min_length=1)


class StageBody(MutationBody):
    stage: Any = None


class FavoriteBody(BaseModel):
    model_config = ConfigDict(extra="allow")

    isFavorite: bool = False


class BulkDeleteBody(BaseModel):
    ids: list[str] = Field(default_factory=list)
    versions: dict[str, int] = Field(default_factory=dict)


class AttachmentsBody(MutationBody):
    files: list[Any] = Field(default_factory=list)
    attachments: list[Any] = Field(default_factory=list)


class StorageActiveBody(BaseModel):
    active: bool = False


class AppSettingsBody(BaseModel):
    model_config = ConfigDict(extra="allow")


class DriveSourceBody(BaseModel):
    model_config = ConfigDict(extra="allow")


class VerifyResetBody(BaseModel):
    email: str
    code: str


class ResetPasswordBody(BaseModel):
    email: str
    code: str
    password: str
    passwordConfirmation: str = ""


class ChangePasswordBody(BaseModel):
    currentPassword: str
    password: str
    passwordConfirmation: str = ""


class AvatarBody(BaseModel):
    avatar: str
