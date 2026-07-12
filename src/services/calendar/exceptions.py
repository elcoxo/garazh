class CalendarError(Exception):
    """Базовая ошибка работы с внешним календарем."""


class CalendarAuthError(CalendarError):
    """Токен отозван или истек, нужно переподключить аккаунт."""


class UnsupportedCredentialError(CalendarError):
    """Учетка не поддерживается ни одним адаптером."""
