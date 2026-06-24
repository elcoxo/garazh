from datetime import datetime

from pydantic import BaseModel


class EventDraft(BaseModel):
    summary: str
    description: str | None = None
    location: str | None = None
    url: str | None = None
    dtstart: datetime
    dtend: datetime | None = None
    all_day: bool = False
