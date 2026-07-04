class CalendarError(Exception):
    """Базовая ошибка работы с внешним календарём."""


class UnsupportedCredentialError(CalendarError):
    """Учётка не поддерживается ни одним адаптером."""
