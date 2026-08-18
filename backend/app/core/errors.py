from dataclasses import dataclass
@dataclass
class DomainError(Exception):
    code: str
    message: str
    status_code: int = 400
    fields: list[dict] | None = None
