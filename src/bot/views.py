from aiogram.types import InputRichMessage

from models import Event

MONTHS_RU = (
    'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
    'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря',
)


def format_event_datetime(event: Event) -> str:
    date = f'{event.dtstart.day} {MONTHS_RU[event.dtstart.month - 1]} {event.dtstart.year}'
    if event.all_day:
        return f'{date}, весь день'
    time = f'{event.dtstart:%H:%M}'
    if event.dtend is not None:
        time = f'{time} – {event.dtend:%H:%M}'
    return f'{date}, {time}'


def render_event_body(event: Event, *, compact: bool = False) -> list[str]:
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
    event: Event,
    *,
    title: str,
    subtitle: str | None = None,
    footer: str | None = None,
    compact: bool = False,
) -> InputRichMessage:
    parts = [f'<h1>{title}</h1>']
    if subtitle:
        parts.append(subtitle)
    parts.extend(render_event_body(event, compact=compact))
    if footer:
        parts.append(f'<br>{footer}')
    return InputRichMessage(html='<br>'.join(parts))
