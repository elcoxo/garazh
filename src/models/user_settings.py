from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel


class UserSettings(BaseModel):
    __tablename__ = 'user_settings'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, index=True)
    use_auto_add: Mapped[bool] = mapped_column(Boolean, default=False)
    use_original_url: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped['User'] = relationship(back_populates='settings')
