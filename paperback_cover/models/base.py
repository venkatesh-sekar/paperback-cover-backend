from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from paperback_cover.config import settings

if TYPE_CHECKING:
    from paperback_cover.models.user import User

DATABASE_URL = f"postgresql+asyncpg://{settings.postgres.user}:{ settings.postgres.password}@{settings.postgres.host}/{settings.postgres.database}"


class Base(DeclarativeBase):
    pass


class Timestamped(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Modifiable(Base):
    __abstract__ = True

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class UserGenerated(Timestamped):
    __abstract__ = True

    owner: Mapped[UUID] = mapped_column(ForeignKey("user.id"), index=True)

    def is_authorised(self, user: "User") -> bool:
        return self.owner == user.id or user.is_superuser
