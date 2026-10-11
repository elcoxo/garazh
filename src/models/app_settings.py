from sqlalchemy import Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class AppSettings(BaseModel):
    __tablename__ = 'app_settings'
    __table_args__ = (
        CheckConstraint('id = 1', name='single_row'),
    )

    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
