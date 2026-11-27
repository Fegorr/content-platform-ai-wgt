from pydantic import BaseModel


class TokenResponse(BaseModel):
    """The access token returned by a successful login."""

    access_token: str
    token_type: str
