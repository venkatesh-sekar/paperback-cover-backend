from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from paperback_cover.models.base import Timestamped, UserGenerated


class UserAsset(UserGenerated, Timestamped):
    __tablename__ = "user_asset"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    path: Mapped[str]
    type: Mapped[str]
