from sqlalchemy import Boolean, CheckConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel
from models.enums import AIProvider


class AppSettings(BaseModel):
    __tablename__ = 'app_settings'
    __table_args__ = (
        CheckConstraint('id = 1', name='single_row'),
    )

    ai_priority: Mapped[AIProvider] = mapped_column(
        Enum(AIProvider, name='ai_provider'),
        default=AIProvider.GEMINI,
    )
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
