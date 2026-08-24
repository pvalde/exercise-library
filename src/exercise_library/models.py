from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Exercise:
    prompt: str
    answer: str
    identifier: str | None = None
    id: UUID | None = None
