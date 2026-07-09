from abc import ABC, abstractmethod

from services.ai.schemas import EventDraft
from services.calendar.schemas import CalendarInfo


class CalendarProvider(ABC):
    @abstractmethod
    async def list_calendars(self) -> list[CalendarInfo]: ...

    @abstractmethod
    async def create_event(self, calendar_id: str, event: EventDraft, timezone: str) -> str: ...

    @abstractmethod
    async def update_event(self, calendar_id: str, external_event_id: str, event: EventDraft, timezone: str) -> None: ...

    @abstractmethod
    async def delete_event(self, calendar_id: str, external_event_id: str) -> None: ...
