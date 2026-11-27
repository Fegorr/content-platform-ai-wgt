from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.auth.jwt import decode_access_token
from src.services.auth_service import AuthService
from src.utils.dependencies import get_auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Return the logged-in user, or raise 401 if the token is invalid or the user is unknown."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error
    user = auth_service.get_user_by_id(payload["sub"])
    if user is None:
        raise credentials_error
    return user
