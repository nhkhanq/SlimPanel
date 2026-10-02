from app.security import (
    create_session_token,
    generate_totp_secret,
    hash_password,
    read_session_token,
    totp_code,
    verify_password,
    verify_totp,
)


def test_password_roundtrip():
    stored = hash_password("correct horse battery")
    assert verify_password("correct horse battery", stored)
    assert not verify_password("wrong password", stored)


def test_password_hash_is_salted():
    assert hash_password("same") != hash_password("same")


def test_verify_rejects_malformed_hash():
    assert not verify_password("x", "not-a-hash")
    assert not verify_password("x", "md5$deadbeef")


def test_session_token_roundtrip():
    token = create_session_token("admin")
    assert read_session_token(token) == "admin"
    assert read_session_token(token + "tampered") is None


def test_totp_accepts_current_code():
    secret = generate_totp_secret()
    assert verify_totp(secret, totp_code(secret))
    assert not verify_totp(secret, "000000") or totp_code(secret) == "000000"


def test_totp_rejects_garbage():
    secret = generate_totp_secret()
    assert not verify_totp(secret, "abcdef")
    assert not verify_totp(secret, "")
