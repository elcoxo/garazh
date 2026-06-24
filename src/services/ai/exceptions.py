# AIDisabledError используется и новой версией (agent.py).
# ExtractionError — LEGACY от ручного failover-реквестера (requester.py).


class ExtractionError(Exception):


class AIDisabledError(Exception):
    """ИИ выключен в app settings"""
