from datetime import datetime, timedelta
from typing import Any
from unittest.mock import patch

from fastapi import HTTPException, status
import pytest

from miapeer.auth import jwt
from pytest_lazy_fixtures import lf as lazy_fixture


class TestEncodeJwt:
    @pytest.mark.parametrize("jwk_value", [None, ""])
    def test_raises_exception_if_no_jwk(
        self, jwk_value: str, valid_jwt_data: dict[str, str | int | None]
    ) -> None:
        with patch(f"{jwt.__name__}.get_jwk", return_value=jwk_value):
            with pytest.raises(jwt.JwtException) as exc_info:
                jwt.encode_jwt(data=valid_jwt_data)

        assert str(exc_info.value) == jwt.JwtErrorMessage.INVALID_JWK.value

    def test_uses_default_expiration(self) -> None:
        with patch(f"{jwt.__name__}.datetime") as mock_datetime:
            # Now, plus 15 minutes
            mock_datetime.now.return_value = datetime(2024, 2, 13, 11, 22, 33, 0)

            returned_jwt = jwt.encode_jwt(data={"sub": "aaa", "exp": None})
            print(f"\n{returned_jwt = }\n")

        assert (
            returned_jwt
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYWEiLCJleHAiOjE3MDc4MjQyNTN9.oznfN4jz4VVp_6iLVivnPJXafrjn2lG1re99DNhusC0"
        )

    def test_explicit_expiration_overrides_token_data(self) -> None:
        with patch(f"{jwt.__name__}.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 2, 13, 11, 22, 33, 0)

            returned_jwt = jwt.encode_jwt(
                data={"sub": "aaa", "exp": None}, expires_delta=timedelta(days=1)
            )
            print(f"\n{returned_jwt = }\n")

        assert (
            returned_jwt
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYWEiLCJleHAiOjE3MDc5MDk3NTN9.Fjlg3oc_9Sjjim5P2AD7pJctNV7sUTV9XgVIxtimltM"
        )

    def test_use_expiration_in_token_data(
        self, valid_jwt_data: dict[str, str | int | None], jwk: str
    ) -> None:
        # Date provided in valid_jwt_data is 7752937429 seconds after the epoch, which is 2024-02-13 11:22:09 UTC
        returned_jwt = jwt.encode_jwt(data=valid_jwt_data)
        print(f"\n{returned_jwt = }\n")

        assert (
            returned_jwt
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXAubmF2YXJyYUBtaWFwZWVyLmNvbSIsImV4cCI6Nzc1MjkzNzQyOX0.xd_iGTLwRP2-csh0-6QiZyCn_S3sxm_YEUaZqDoaWXI"
        )


class TestDecodeJwt:
    @pytest.mark.parametrize("jwk_value", [None, ""])
    def test_raises_exception_if_no_jwk(self, jwk_value: str, valid_jwt: str) -> None:
        with patch(f"{jwt.__name__}.get_jwk", return_value=jwk_value):
            with pytest.raises(jwt.JwtException) as exc_info:
                jwt.decode_jwt(token=valid_jwt)

        assert str(exc_info.value) == jwt.JwtErrorMessage.INVALID_JWK.value

    def test_decodes_token(
        self,
        jwk: str,
        valid_jwt: str,
        valid_jwt_data: jwt.TokenData,
    ) -> None:
        with patch(f"{jwt.__name__}.get_jwk") as mock_get_jwk:
            mock_get_jwk.return_value = jwk

            token_data = jwt.decode_jwt(
                token=valid_jwt,
            )

        print(f"\n{token_data = }\n")
        print(f"\n{valid_jwt_data = }\n")

        assert token_data == valid_jwt_data

    @pytest.mark.parametrize(
        "token_data,exception_value",
        [
            # No token
            ({}, "Token payload is incomplete"),
            # Missing username
            ({"exp": 1234567890}, "Token payload is incomplete"),
            # Missing expiration
            ({"sub": "aaa"}, "Token payload is incomplete"),
            # Expired token
            (
                lazy_fixture("expired_jwt_data"),
                "Could not validate credentials",
            ),
        ],
    )
    def test_invalid_token_raises_exception(
        self, token_data: dict[str, Any], valid_jwt: str, exception_value: str
    ) -> None:
        with patch(f"{jwt.__name__}.jwt.decode", return_value=token_data):
            with pytest.raises(HTTPException) as exc_info:
                jwt.decode_jwt(token=valid_jwt)

        print(f"\n{exc_info.value.detail = }\n")
        print(f"\n{exception_value = }\n")

        assert exc_info.value.detail == exception_value

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
