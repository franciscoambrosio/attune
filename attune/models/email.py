from enum import Enum
from pydantic import BaseModel


class TriageLabel(str, Enum):
    URGENT = "URGENT"
    SOON = "SOON"
    LATER = "LATER"
    IGNORE = "IGNORE"


class Email(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    timestamp: str


class TriageResult(BaseModel):
    email_id: str
    label: TriageLabel
    reasoning: str
