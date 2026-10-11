from sqlalchemy import Boolean, Enum, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel
from models.enums import AIProvider


class AIModel(BaseModel):
    __tablename__ = 'ai_models'
    __table_args__ = (
        UniqueConstraint('provider', 'name', name='provider_name'),
    )

    provider: Mapped[AIProvider] = mapped_column(Enum(AIProvider, name='ai_provider'))
    name: Mapped[str] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer, default=0)
    last_used_model: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
