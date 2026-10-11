class AIDisabledError(Exception):
    """ИИ выключен в app settings."""


class AIUnavailableError(Exception):
    """Провайдеры ИИ не смогли обработать запрос."""
