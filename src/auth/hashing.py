from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return an argon2 hash of the password, with a new salt each call."""
    return _password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Return True if the password matches the hash; False for a wrong password or a malformed hash."""
    try:
        return _password_hash.verify(password, hashed_password)
    except PwdlibError:
        return False
