from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.caldav_credential import CalDAVCredential
    from models.oauth_credential import OAuthCredential


class UserCalendar(BaseModel):
    __tablename__ = "user_calendars"
    __table_args__ = (
        CheckConstraint(
            "(oauth_credential_id IS NOT NULL)::int + (caldav_credential_id IS NOT NULL)::int = 1",
            name="single_credential",
        ),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    oauth_credential_id: Mapped[int | None] = mapped_column(ForeignKey("oauth_credentials.id"))
    caldav_credential_id: Mapped[int | None] = mapped_column(ForeignKey("caldav_credentials.id"))
    calendar_id: Mapped[str] = mapped_column(String(256))
    calendar_name: Mapped[str | None] = mapped_column(String(256))
    calendar_timezone: Mapped[str] = mapped_column(String(64), default='Europe/Moscow')
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="calendars")
    oauth_credential: Mapped["OAuthCredential | None"] = relationship(back_populates="calendars")
    caldav_credential: Mapped["CalDAVCredential | None"] = relationship(back_populates="calendars")
    user_events: Mapped[list["UserEvent"]] = relationship(
        back_populates="calendar",
        cascade="all, delete-orphan",
    )

    @property
    def credential(self) -> "OAuthCredential | CalDAVCredential":
        cred = self.oauth_credential or self.caldav_credential
        assert cred is not None, "UserCalendar without credential violates single_credential CheckConstraint"
        return cred
