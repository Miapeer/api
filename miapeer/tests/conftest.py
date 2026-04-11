import pytest

from miapeer.auth.jwt import TokenData


@pytest.fixture
def jwk() -> str:
    return "super secret key"


@pytest.fixture
def valid_jwt() -> str:
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXAubmF2YXJyYUBtaWFwZWVyLmNvbSIsImV4cCI6Nzc1MjkzNzQyOX0.RYipfri10zKHHyAk8Vg_fRfQmKXpp_7nyjuaKRUIWmk"


@pytest.fixture
def valid_jwt_data() -> dict[str, str | int | None]:
    return {"sub": "jep.navarra@miapeer.com", "exp": 7752937429}


@pytest.fixture
def expired_jwt() -> str:
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZWZmLm5hdmFycmFAbWlhcGVlci5jb20iLCJleHAiOjE2Nzc5ODU1NjV9.MIKPImtnO63dNmez_QsFTkuzXeLs5kxtGXJp5oEQFUY"


@pytest.fixture
def expired_jwt_data() -> TokenData:
    return {"sub": "jeff.navarra@miapeer.com", "exp": 1677985565}


@pytest.fixture
def jwt_missing_sub() -> str:
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIiLCJleHAiOjc3NTI5Mzc0Mjl9.x37UcZkx7s_QaFpRGSCDqleB6N3rMBeknCG6iMReejM"
