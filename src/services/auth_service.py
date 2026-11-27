from src.auth.hashing import hash_password, verify_password

# Checked when the email is unknown, so unknown emails and wrong passwords take
# about the same time and timing can't reveal which emails exist.
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing")


class AuthService:
    """User authentication for the API: checking credentials and looking up the logged-in user."""

    def __init__(self, user_repository):
        self._user_repository = user_repository

    def authenticate_user(self, email: str, password: str) -> dict | None:
        """Return the user for a correct email and password, otherwise None."""
        user = self._user_repository.get_by_email(email.lower())
        if user is None:
            verify_password(password, _DUMMY_PASSWORD_HASH)
            return None
        if not verify_password(password, user["hashed_password"]):
            return None
        return user

    def get_user_by_id(self, user_id: str) -> dict | None:
        """Return the user without hashed_password, or None if not found."""
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            return None
        return {key: value for key, value in user.items() if key != "hashed_password"}
