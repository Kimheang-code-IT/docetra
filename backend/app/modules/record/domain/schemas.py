from pydantic import BaseModel, ConfigDict, Field


class RecordPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    title: str | None = None
    status: str | None = None
    stage: str | None = None
    recordTypeCode: str | None = None
    recordTime: str | None = None
    recordContent: str | None = None
    recordTag: str | None = None
    version: int | None = None


class MeetingAssignTopic(BaseModel):
    model_config = ConfigDict(extra="allow")

    topicId: str | None = None
    topicTitle: str | None = None
    sortOrder: int | None = None


class MeetingReorder(BaseModel):
    model_config = ConfigDict(extra="allow")

    topicId: str | None = None
    orderedMeetingIds: list[str] = []


class MeetingLinkDrive(BaseModel):
    model_config = ConfigDict(extra="allow")

    displayName: str | None = None
    mimeType: str | None = None
    sizeBytes: int | None = None
    webViewLink: str | None = None
    driveFileId: str | None = None
