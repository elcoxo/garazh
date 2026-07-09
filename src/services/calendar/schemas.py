from pydantic import BaseModel


class CalendarInfo(BaseModel):
    id: str
    name: str
    timezone: str
