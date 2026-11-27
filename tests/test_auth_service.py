from unittest.mock import Mock, patch

from src.auth.hashing import hash_password
from src.services.auth_service import AuthService

PASSWORD = "louise_pass_1"


def make_stored_user():
    return {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Louise",
        "email": "louise@test.com",
        "hashed_password": hash_password(PASSWORD),
        "role": "user",
    }


def test_authenticate_user_lowercases_email():
    """The email is lowercased before the repository lookup."""
    repository = Mock()
    repository.get_by_email.return_value = make_stored_user()
    AuthService(repository).authenticate_user("Louise@Test.com", PASSWORD)
    repository.get_by_email.assert_called_once_with("louise@test.com")


def test_authenticate_user_right_password():
    """The right password returns the stored user dict."""
    stored = make_stored_user()
    repository = Mock()
    repository.get_by_email.return_value = stored
    assert AuthService(repository).authenticate_user("louise@test.com", PASSWORD) == stored


def test_authenticate_user_wrong_password():
    """A wrong password returns None and verifies once against the stored hash."""
    stored = make_stored_user()
    repository = Mock()
    repository.get_by_email.return_value = stored
    with patch("src.services.auth_service.verify_password", return_value=False) as verify:
        result = AuthService(repository).authenticate_user("louise@test.com", "wrong_pass_1")
    assert result is None
    verify.assert_called_once_with("wrong_pass_1", stored["hashed_password"])


def test_authenticate_user_unknown_email():
    """An unknown email returns None but still verifies once against a dummy argon2 hash."""
    repository = Mock()
    repository.get_by_email.return_value = None
    with patch("src.services.auth_service.verify_password", return_value=False) as verify:
        result = AuthService(repository).authenticate_user("nobody@test.com", PASSWORD)
    assert result is None
    verify.assert_called_once()
    args = verify.call_args.args
    assert args[0] == PASSWORD
    assert args[1].startswith("$argon2")


def test_get_user_by_id_removes_hashed_password():
    """get_user_by_id returns id, name, email and role only."""
    stored = make_stored_user()
    repository = Mock()
    repository.get_by_id.return_value = stored
    result = AuthService(repository).get_user_by_id(stored["id"])
    repository.get_by_id.assert_called_once_with(stored["id"])
    assert result == {
        "id": stored["id"],
        "name": "Louise",
        "email": "louise@test.com",
        "role": "user",
    }


def test_get_user_by_id_not_found():
    """get_user_by_id returns None when the repository finds nobody."""
    repository = Mock()
    repository.get_by_id.return_value = None
    assert AuthService(repository).get_user_by_id("missing-id") is None
    repository.get_by_id.assert_called_once_with("missing-id")


def test_get_user_by_id_keeps_repository_dict_unchanged():
    """get_user_by_id does not remove hashed_password from the dict the repository returned."""
    stored = make_stored_user()
    repository = Mock()
    repository.get_by_id.return_value = stored
    AuthService(repository).get_user_by_id(stored["id"])
    assert "hashed_password" in stored
