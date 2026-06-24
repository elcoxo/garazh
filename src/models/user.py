from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    tg_username: Mapped[str | None] = mapped_column(String(64))
    tg_full_name: Mapped[str | None] = mapped_column(String(256))

    oauth_credentials: Mapped[list["OAuthCredential"]] = relationship(back_populates="user")
    caldav_credentials: Mapped[list["CalDAVCredential"]] = relationship(back_populates="user")
    calendars: Mapped[list["UserCalendar"]] = relationship(back_populates="user")
    settings: Mapped["UserSettings | None"] = relationship(back_populates="user")
    user_events: Mapped[list["UserEvent"]] = relationship(back_populates="user")

    @property
    def calendar(self) -> "UserCalendar | None":
        return self.calendars[0] if self.calendars else None

    @property
    def oauth_credential(self) -> "OAuthCredential | None":
        return self.oauth_credentials[0] if self.oauth_credentials else None
