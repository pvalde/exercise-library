from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    prompt: str
    answer: str
    id: int | None = None
