# type: ignore
from typing import Any, Dict

from fastapi import Response, status
from fastapi_users.authentication import (
    AuthenticationBackend,
)
import secrets
from fastapi_users.authentication.strategy import Strategy
from fastapi_users.authentication.strategy.db import (
    DatabaseStrategy,
)
from fastapi_users import models

from {{cookiecutter.project_name}}.settings import settings


class AutoRedirectSSOCookieBackend(AuthenticationBackend):
    async def login(self, strategy: Strategy, user: Any) -> Response:
        response = await super().login(strategy, user)
        response.status_code = status.HTTP_302_FOUND
        response.headers["Location"] = settings.REDIRECT_LOGIN_URL
        return response


class APIDatabaseStrategy(DatabaseStrategy):
    def _create_access_token_dict(self, user: models.UP) -> Dict[str, Any]:
        token = "pat_" + secrets.token_urlsafe(128)
        return {"token": token, "user_id": user.id}
