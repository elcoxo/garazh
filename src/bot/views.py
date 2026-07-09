from dataclasses import dataclass
from datetime import datetime

from aiogram.types import InputRichMessage

from models import Event

MONTHS_RU = (
    'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
    'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря',
)

FIELD_LABELS = {
    'summary': 'название',
    'location': 'место',
    'dtstart': 'дата',
    'description': 'описание',
    'url': 'ссылка',
}

EDIT_EVENT_TITLE = 'Изменить событие'
EDIT_EVENT_FOOTER = 'выберите поле для редактирования'


@dataclass(slots=True)
class EventView:
    id: int
    summary: str
    description: str | None
    location: str | None
    url: str | None
    dtstart: datetime
    dtend: datetime | None
    all_day: bool

    @classmethod
    def with_date_state(cls, event: Event, state: dict) -> 'EventView':
        return cls(
            id=event.id,
            summary=event.summary,
            description=event.description,
            location=event.location,
            url=event.url,
            dtstart=datetime.fromisoformat(state['dtstart_iso']),
            dtend=datetime.fromisoformat(state['dtend_iso']) if state.get('dtend_iso') else None,
            all_day=state['all_day'],
        )


def format_event_datetime(event: 'Event | EventView') -> str:
    date = f'{event.dtstart.day} {MONTHS_RU[event.dtstart.month - 1]} {event.dtstart.year}'
    if event.all_day:
        return f'{date}, весь день'
    time = f'{event.dtstart:%H:%M}'
    if event.dtend is not None:
        time = f'{time} – {event.dtend:%H:%M}'
    return f'{date}, {time}'


def render_event_body(event: 'Event | EventView', *, compact: bool = False) -> list[str]:
    info = [f'<b>{event.summary}</b>', f'📅 {format_event_datetime(event)}']
    if event.location:
        info.append(f'📍 {event.location}')

    parts = ['<br>'.join(info)]
    if compact:
        return parts
    if event.description:
        parts.append(f'<blockquote expandable>{event.description}</blockquote>')
    if event.url:
        parts.append(f'🔗 {event.url}')
    return parts


def build_event_message(
        event: 'Event | EventView',
        *,
        title: str,
        subtitle: str | None = None,
        footer: str | None = None,
        compact: bool = False,
) -> InputRichMessage:
    parts = [f'<h1>{title}</h1>']
    if subtitle:
        parts.append(f'{subtitle}<br>')
    parts.extend(render_event_body(event, compact=compact))
    if footer:
        parts.append(f'<br>{footer}')
    return InputRichMessage(html='<br>'.join(parts))


def build_edit_field_message(field: str, current: str | None) -> InputRichMessage:
    parts = [f'<h1>Новое {FIELD_LABELS[field]}</h1>']
    if current:
        parts.append(f'<b>{current}</b>')
    parts.append('Отправь сообщением')
    return InputRichMessage(html='<br>'.join(parts))
