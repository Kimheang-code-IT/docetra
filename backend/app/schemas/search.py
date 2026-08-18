from pydantic import BaseModel
class SearchRequest(BaseModel): q:str; hitIds:list[str]=[]
