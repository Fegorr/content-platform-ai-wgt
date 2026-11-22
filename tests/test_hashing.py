from src.auth.hashing import hash_password, verify_password


def test_hash_password_returns_argon2_hash():
    """hash_password returns an argon2 hash, not the plain password."""
    hashed = hash_password("louise_pass_1")
    assert hashed.startswith("$argon2")
    assert hashed != "louise_pass_1"


def test_hash_password_twice_gives_different_hashes():
    """Hashing the same password twice gives two different hashes."""
    assert hash_password("louise_pass_1") != hash_password("louise_pass_1")


def test_verify_password_correct():
    """verify_password is True for the right password."""
    hashed = hash_password("louise_pass_1")
    assert verify_password("louise_pass_1", hashed) is True


def test_verify_password_wrong():
    """verify_password is False for a wrong password."""
    hashed = hash_password("louise_pass_1")
    assert verify_password("wrong_pass_99", hashed) is False


def test_verify_password_malformed_hash():
    """verify_password returns False, not an error, for a malformed hash."""
    assert verify_password("louise_pass_1", "not-a-hash") is False


def test_verify_password_empty_hash():
    """verify_password returns False, not an error, for an empty hash."""
    assert verify_password("louise_pass_1", "") is False
