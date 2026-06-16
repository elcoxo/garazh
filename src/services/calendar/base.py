from abc import ABC, abstractmethod

from pydantic import BaseModel

from services.ai.base import ParsedEvent


class CalendarInfo(BaseModel):
    id: str
    name: str


class CalendarProvider(ABC):
    @abstractmethod
    async def list_calendars(self) -> list[CalendarInfo]: ...

    @abstractmethod
    async def create_event(self, calendar_id: str, event: ParsedEvent) -> str: ...
