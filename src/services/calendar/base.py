from abc import ABC, abstractmethod

from services.ai.schemas import EventDraft
from services.calendar.schemas import CalendarInfo


class CalendarProvider(ABC):
    @abstractmethod
    async def list_calendars(self) -> list[CalendarInfo]: ...

    @abstractmethod
    async def create_event(self, calendar_id: str, event: EventDraft) -> str: ...
