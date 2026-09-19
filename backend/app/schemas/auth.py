from typing import Optional
from pydantic import BaseModel


class TokenExchangeRequest(BaseModel):
    firebase_id_token: str
    locale: Optional[str] = "en"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
