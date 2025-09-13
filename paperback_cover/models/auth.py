from fastapi_users_db_sqlalchemy import SQLAlchemyBaseOAuthAccountTableUUID
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID

from paperback_cover.models.base import Base, Timestamped


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    pass


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Timestamped):
    pass
