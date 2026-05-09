from miapeer.auth import jwt
from unittest.mock import Mock, patch


class TestEncodeJwt:
    @patch(f"{jwt.__name__}.os")
    def test_success(
        self,
        mock_env: Mock,
        jwk: str,
        valid_jwt_data: dict[str, str | int | None],
        valid_jwt: str,
    ):
        mock_env.environ = {"JWT_SECRET_KEY": jwk}

        returned_jwt = jwt.encode_jwt(data=valid_jwt_data)

        assert returned_jwt == valid_jwt


class TestDecodeJwt:
    @patch(f"{jwt.__name__}.os")
    def test_success(
        self,
        mock_env: Mock,
        jwk: str,
        valid_jwt_data: dict[str, str | int | None],
        valid_jwt: str,
    ):
        mock_env.environ = {"JWT_SECRET_KEY": jwk}

        returned_jwt_data = jwt.decode_jwt(token=valid_jwt)

        assert returned_jwt_data == valid_jwt_data
