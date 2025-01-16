# type: ignore
import uuid

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, schemas
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,

    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_users_db_sqlalchemy.access_token import (
    SQLAlchemyAccessTokenDatabase,
    SQLAlchemyBaseAccessTokenTableUUID,
)

from {{cookiecutter.project_name}}.db.base import Base
from {{cookiecutter.project_name}}.db.dependencies import get_db_session
from {{cookiecutter.project_name}}.settings import settings

from {{cookiecutter.project_name}}.auth.backends import (
    AutoRedirectSSOCookieBackend,
    APIDatabaseStrategy
)


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Represents a user entity."""


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Represents a read command for a user."""


class UserCreate(schemas.BaseUserCreate):
    """Represents a create command for a user."""


class UserUpdate(schemas.BaseUserUpdate):
    """Represents an update command for a user."""


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """Manages a user session and its tokens."""
    reset_password_token_secret = settings.users_secret
    verification_token_secret = settings.users_secret


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    description: Mapped[str] = mapped_column(String, nullable=True)
    pass

async def get_access_token_db(session: AsyncSession = Depends(get_db_session)):
    """Asynchronous generator function to provide an instance of SQLAlchemyAccessTokenDatabase.
    This function is intended to be used as a dependency in FastAPI routes to get an access token database session.
    Args:
        session (AsyncSession): An asynchronous SQLAlchemy session, provided by the get_db_session dependency.

    Yields:
        SQLAlchemyAccessTokenDatabase: An instance of the access token database.
    """
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)

async def get_user_db(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyUserDatabase:
    """
    Yield a SQLAlchemyUserDatabase instance.

    :param session: asynchronous SQLAlchemy session.
    :yields: instance of SQLAlchemyUserDatabase.
    """
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)) -> UserManager:
    """
    Yield a UserManager instance.

    :param user_db: SQLAlchemy user db instance
    :yields: an instance of UserManager.
    """
    yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy:
    """
    Return a JWTStrategy in order to instantiate it dynamically.

    :returns: instance of JWTStrategy with provided settings.
    """
    return JWTStrategy(secret=settings.users_secret, lifetime_seconds=None)

def get_persistent_token_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy:
    return DatabaseStrategy(access_token_db, lifetime_seconds=172800)


{%- if cookiecutter.jwt_auth == "True" %}
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
auth_jwt = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
{%- endif %}

{%- if cookiecutter.cookie_auth == "True" %}
cookie_transport = CookieTransport()
auth_cookie = AuthenticationBackend(
    name="cookie", transport=cookie_transport, get_strategy=get_jwt_strategy
)
{%- endif %}

user_auth_sso_cookie = AutoRedirectSSOCookieBackend(
    name="sso_cookie",
    transport=cookie_transport,
    get_strategy=get_persistent_token_strategy,
)

backends = [
    {%- if cookiecutter.cookie_auth == "True" %}
    auth_cookie,
    {%- endif %}
    {%- if cookiecutter.jwt_auth == "True" %}
    auth_jwt,
    {%- endif %}
    user_auth_sso_cookie
]

api_users = FastAPIUsers[User, uuid.UUID](get_user_manager, backends)

current_active_user = api_users.current_user(active=True)
