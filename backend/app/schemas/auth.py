from pydantic import BaseModel
class AuthUser(BaseModel):
    id:str; name:str; email:str; role:str|None=None; avatar:str|None=None; permissions:list[str]=[]; pageAccess:list[str]=[]
