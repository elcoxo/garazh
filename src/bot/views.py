from dataclasses import dataclass
from datetime import datetime

from aiogram.types import InputRichMessage
from aiogram_i18n.lazy import LazyProxy as _

from models import Event

MONTHS_RU = (
    'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
    'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря',
)

FIELD_LABELS = {
    'summary': 'Новое название',
    'location': 'Новое место',
    'dtstart': 'Новая дата',
    'description': 'Новое описание',
    'url': 'Новая ссылка',
}

EDIT_EVENT_TITLE = _('title-edit-event')
EDIT_EVENT_FOOTER = _('footer-edit-event')


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
        parts.append(f'<blockquote expandable>{event.description.replace('\n', '<br>')}</blockquote>')
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
    title = getattr(title, 'data', title)
    subtitle = getattr(subtitle, 'data', subtitle)
    footer = getattr(footer, 'data', footer)
    body_parts = []
    if subtitle:
        body_parts.append(f'{subtitle}<br>')
    body_parts.extend(render_event_body(event, compact=compact))
    if footer:
        body_parts.append(footer)
    return InputRichMessage(html=f'<h1>{title}</h1>' + '<br>'.join(body_parts))


def build_edit_field_message(field: str, current: str | None) -> InputRichMessage:
    body_parts = []
    if current:
        body_parts.append(f'<b>{current}</b>')
    body_parts.append('Отправь сообщением')
    return InputRichMessage(html=f'<h1>{FIELD_LABELS[field]}</h1>' + '<br>'.join(body_parts))
