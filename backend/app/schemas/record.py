from pydantic import BaseModel,ConfigDict
class RecordPayload(BaseModel): model_config=ConfigDict(extra="allow")
