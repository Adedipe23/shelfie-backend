from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Token schema for authentication responses."""

    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Token payload schema for JWT decoding."""

    sub: Optional[str] = None
    exp: Optional[float] = None
