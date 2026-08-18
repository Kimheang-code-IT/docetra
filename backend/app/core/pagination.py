from dataclasses import dataclass
@dataclass(frozen=True)
class Page:
    number: int = 1
    limit: int = 20
    @classmethod
    def bounded(cls, number: int = 1, limit: int = 20): return cls(max(number, 1), min(max(limit, 1), 200))
