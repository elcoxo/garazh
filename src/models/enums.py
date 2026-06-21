from enum import StrEnum


class TextChoices(StrEnum):
    label: str

    def __new__(cls, value: str, label: str) -> 'TextChoices':
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.label = label
        return obj


class ProviderSlug(TextChoices):
    GOOGLE = 'google', 'Google Calendar'
    YANDEX = 'yandex', 'Яндекс Календарь'
    MAILRU = 'mailru', 'Mail.ru Календарь'
    CALDAV = 'caldav', 'CalDAV'
