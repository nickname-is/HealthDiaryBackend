from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TokenPayload(BaseModel):
    exp: int
    sub: int


class RefreshRequest(BaseModel):
    refresh_token: str
    fingerprint: Optional[str] = None


class LogoutRequest(BaseModel):
    refresh_token: str
