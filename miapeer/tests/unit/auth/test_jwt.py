from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from pytest_lazyfixture import lazy_fixture

from miapeer.auth import jwt


class TestEncodeJwt:
    def test_missing_jwk_raises_exception(self) -> None:
        with pytest.raises(jwt.JwtException) as exc_info:
            jwt.encode_jwt(jwt_key="", data={"sub": "aaa", "exp": 1111})

        assert str(exc_info.value) == jwt.JwtErrorMessage.INVALID_JWK

    @patch(f"{jwt.__name__}.datetime")
    def test_uses_default_expiration(self, mocked_datetime: Mock, jwk: str) -> None:
        mocked_datetime.utcnow.return_value = datetime(2024, 2, 13, 11, 22, 33, 0)

        returned_jwt = jwt.encode_jwt(jwt_key=jwk, data={"sub": "aaa", "exp": None})

        assert (
            returned_jwt
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYWEiLCJleHAiOjE3MDc4MjQyNTN9.jaZUBmKWot0wA7Bgln-0IHQRRJeKbqLxgXc1N7J3SHM"
        )

    @patch(f"{jwt.__name__}.datetime", wraps=datetime)
    def test_explicit_expiration_overrides_token_data(self, mocked_datetime: Mock, jwk: str) -> None:
        mocked_datetime.utcnow.return_value = datetime(2024, 2, 13, 11, 22, 33, 0)

        returned_jwt = jwt.encode_jwt(jwt_key=jwk, data={"sub": "aaa", "exp": None}, expires_delta=timedelta(days=1))

        assert (
            returned_jwt
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYWEiLCJleHAiOjE3MDc5MDk3NTN9.X8Gy1GQBn3aFJarYeV3kQAeFOC7lx0SFaH-Yd2-YP08"
        )

    def test_use_expiration_in_token_data(self, valid_jwt_data: jwt.TokenData, jwk: str) -> None:
        returned_jwt = jwt.encode_jwt(jwt_key=jwk, data=valid_jwt_data)

        assert (
            returned_jwt
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXAubmF2YXJyYUBtaWFwZWVyLmNvbSIsImV4cCI6Nzc1MjkzNzQyOX0.RYipfri10zKHHyAk8Vg_fRfQmKXpp_7nyjuaKRUIWmk"
        )


class TestDecodeJwt:
    def test_decodes_token(self, valid_jwt: str, jwk: str, valid_jwt_data: jwt.TokenData) -> None:
        token_data = jwt.decode_jwt(
            token=valid_jwt,
            jwt_key=jwk,
        )
        assert token_data == valid_jwt_data

    def test_missing_jwk_raises_exception(self) -> None:
        with pytest.raises(jwt.JwtException) as exc_info:
            jwt.decode_jwt(jwt_key="", token="")

        assert str(exc_info.value) == jwt.JwtErrorMessage.INVALID_JWK

    @pytest.mark.parametrize(
        "token,exception_value",
        [
            # No token
            ("", jwt.JwtErrorMessage.INVALID_TOKEN),
            # Invalid token
            ("some.bad.token", jwt.JwtErrorMessage.INVALID_TOKEN),
            # Expired token
            (
                lazy_fixture("expired_jwt"),
                jwt.JwtErrorMessage.INVALID_TOKEN,
            ),
        ],
    )
    def test_invalid_token_raises_exception(self, jwk: str, token: str, exception_value: str) -> None:
        with pytest.raises(jwt.JwtException) as exc_info:
            jwt.decode_jwt(token=token, jwt_key=jwk)

        assert str(exc_info.value) == exception_value
