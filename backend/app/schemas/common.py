from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field
T=TypeVar("T")
class ApiResponse(BaseModel,Generic[T]): data:T; meta:dict[str,Any]|None=None
class ListQuery(BaseModel):
    model_config=ConfigDict(extra="allow")
    q:str|None=None; page:int=Field(1,ge=1); limit:int=Field(20,ge=1,le=200); sort:str="-updatedAt"; status:str|None=None; stage:str|None=None
