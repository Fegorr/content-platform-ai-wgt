from fastapi import Depends

from src.db.database import get_users_collection
from src.db.user_repository import UserRepository
from src.services.auth_service import AuthService


def get_user_repository() -> UserRepository:
    """Return a user repository on the users collection."""
    return UserRepository(get_users_collection())


def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    """Return an auth service that uses the given user repository."""
    return AuthService(user_repository)
