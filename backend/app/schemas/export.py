from pydantic import BaseModel,ConfigDict
class ExportRequest(BaseModel): model_config=ConfigDict(extra="allow"); resource:str
