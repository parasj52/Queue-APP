# Models for job queue_app (Python dataclasses)
from dataclasses import dataclass
from typing import Optional

@dataclass
class Job:
    id: str
    payload: str
    status: str
    retries: int
    user: str
    idempotency_key: Optional[str]
    created_at: float

@dataclass
class DLQItem:
    id: str
    payload: str
    user: str
    reason: str
    created_at: float
