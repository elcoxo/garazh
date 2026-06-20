from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.enums import ProviderSlug
from models.types import EncryptedStr


class OAuthCredential(BaseModel):
    __tablename__ = "oauth_credentials"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[ProviderSlug] = mapped_column(SAEnum(ProviderSlug))
    access_token: Mapped[str] = mapped_column(EncryptedStr)
    refresh_token: Mapped[str | None] = mapped_column(EncryptedStr, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email: Mapped[str | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="oauth_credentials")
    calendars: Mapped[list["UserCalendar"]] = relationship(back_populates="oauth_credential")
