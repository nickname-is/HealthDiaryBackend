from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshTokenCreate(BaseModel):
    user_id: int
    token: str
    expire_at: datetime
    fingerprint: str | None = None


class TokenPayload(BaseModel):
    exp: int
    sub: int


class RefreshRequest(BaseModel):
    refresh_token: str
    fingerprint: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str
