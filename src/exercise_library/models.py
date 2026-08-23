from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    prompt: str
    answer: str
    identifier: str | None = None
    id: int | None = None
