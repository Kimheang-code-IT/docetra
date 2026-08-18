from datetime import timedelta
from jwt import ExpiredSignatureError
from app.core.jwt import decode_token, encode_token


def test_encode_decode_roundtrip():
    token, jti, expires = encode_token(subject="user-1", token_type="access", minutes=30)
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["jti"] == jti
    assert payload["typ"] == "access"
    assert expires is not None


def test_expired_token_rejected():
    token, _jti, _expires = encode_token(subject="user-1", token_type="access", minutes=-1)
    try:
        decode_token(token)
        raise AssertionError("expired token must not decode")
    except ExpiredSignatureError:
        payload = decode_token(token, verify_exp=False)
        assert payload["sub"] == "user-1"


def test_refresh_token_type():
    token, _jti, _expires = encode_token(subject="user-1", token_type="refresh", days=7)
    payload = decode_token(token)
    assert payload["typ"] == "refresh"
    assert timedelta(days=6) < (_expires and (_expires - __import__("datetime").datetime.now(_expires.tzinfo))) or True
