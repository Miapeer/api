import pytest

from miapeer.auth.jwt import (
    JwtErrorMessage,
    JwtException,
    decode_jwt,
    encode_jwt,
)

# from miapeer.dependencies import get_current_active_user


@pytest.fixture
def jwk() -> str:
    return "super secret key"


class TestEncodeJwt:
    def test_missing_jwk_raises_exception(self) -> None:
        with pytest.raises(JwtException) as exc_info:
            encode_jwt(jwt_key="", data={"sub": "aaa", "exp": 111})

        assert str(exc_info.value) == JwtErrorMessage.INVALID_JWK


class TestDecodeJwt:
    def test_missing_jwk_raises_exception(self) -> None:
        with pytest.raises(JwtException) as exc_info:
            decode_jwt(jwt_key="", token="")

        assert str(exc_info.value) == JwtErrorMessage.INVALID_JWK

    @pytest.mark.parametrize(
        "token,exception_value",
        [
            # No token
            ("", JwtErrorMessage.INVALID_TOKEN),
            # Invalid token
            ("some.bad.token", JwtErrorMessage.INVALID_TOKEN),
            # Expired token
            (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZWZmLm5hdmFycmFAbWlhcGVlci5jb20iLCJleHAiOjE2Nzc5ODU1NjV9.gCV8uhqs1QiMQvBVfY4RUiyVwVo7R3Sn7opRY79LeQ8",
                JwtErrorMessage.INVALID_TOKEN,
            ),
        ],
    )
    def test_invalid_token_raises_exception(self, jwk: str, token: str, exception_value: str) -> None:
        with pytest.raises(JwtException) as exc_info:
            decode_jwt(token=token, jwt_key=jwk)

        assert str(exc_info.value) == exception_value
