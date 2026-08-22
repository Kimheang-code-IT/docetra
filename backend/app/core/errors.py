from dataclasses import dataclass, field


@dataclass
class DomainError(Exception):
    code: str
    message: str
    status_code: int = 422
    fields: list[dict] | None = field(default=None)
