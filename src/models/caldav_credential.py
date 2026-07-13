from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.enums import ProviderSlug
from models.types import EncryptedStr


class CalDAVCredential(BaseModel):
    __tablename__ = 'caldav_credentials'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    provider: Mapped[ProviderSlug] = mapped_column(SAEnum(ProviderSlug))
    server_url: Mapped[str | None] = mapped_column(String(512))
    username: Mapped[str] = mapped_column(String(256))
    password: Mapped[str] = mapped_column(EncryptedStr)

    user: Mapped['User'] = relationship(back_populates='caldav_credentials')
    calendars: Mapped[list['UserCalendar']] = relationship(back_populates='caldav_credential')
