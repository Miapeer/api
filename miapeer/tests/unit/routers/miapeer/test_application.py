from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
)
from miapeer.routers.miapeer import application

pytestmark = pytest.mark.asyncio


@pytest.fixture
def application_id() -> int:
    return 12345


@pytest.fixture
def application_name() -> str:
    return "my app name"


@pytest.fixture
def application_url() -> str:
    return "my app url"


@pytest.fixture
def application_description() -> str:
    return "my app desc"


@pytest.fixture
def application_icon() -> str:
    return "my app icon"


@pytest.fixture
def application_display() -> bool:
    return True


class TestGetAll:
    @pytest.fixture
    def expected_sql(self) -> str:
        return f"SELECT miapeer_application.name, miapeer_application.url, miapeer_application.description, miapeer_application.icon, miapeer_application.display, miapeer_application.application_id \nFROM miapeer_application ORDER BY miapeer_application.name"

    @pytest.mark.parametrize("db_all_return_val", [[], "some data", 123])
    async def test_get_all(self, mock_db: Mock, expected_sql: str, db_all_return_val: Any) -> None:
        response = await application.get_all_applications(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == db_all_return_val


class TestCreate:
    @pytest.fixture
    def application_create(
        self,
        application_name: str,
        application_url: str,
        application_description: str,
        application_icon: str,
        application_display: bool,
    ) -> ApplicationCreate:
        return ApplicationCreate(
            name=application_name,
            url=application_url,
            description=application_description,
            icon=application_icon,
            display=application_display,
        )

    @pytest.fixture
    def application_to_add(
        self,
        application_name: str,
        application_url: str,
        application_description: str,
        application_icon: str,
        application_display: bool,
    ) -> Application:
        return Application(
            application_id=None,
            name=application_name,
            url=application_url,
            description=application_description,
            icon=application_icon,
            display=application_display,
        )

    @pytest.mark.parametrize("db_first_return_val", ["some data"])
    async def test_create(
        self,
        application_create: ApplicationCreate,
        application_to_add: Application,
        mock_db: Mock,
    ) -> None:
        await application.create_application(application=application_create, db=mock_db)

        mock_db.add.assert_called_once_with(application_to_add)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(application_to_add)
        # Don't need to test the response here because it's just the updated application_to_add


class TestGet:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_get_with_data(self, application_id: int, mock_db: Mock, db_get_return_val: Any) -> None:
        response = await application.get_application(application_id=application_id, db=mock_db)

        assert response == db_get_return_val

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_get_with_no_data(self, application_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await application.get_application(application_id=application_id, db=mock_db)


class TestDelete:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_delete_with_application_found(
        self, application_id: int, mock_db: Mock, db_get_return_val: Any
    ) -> None:
        response = await application.delete_application(application_id=application_id, db=mock_db)

        mock_db.delete.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        assert response == {"ok": True}

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_delete_with_application_not_found(self, application_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await application.delete_application(application_id=application_id, db=mock_db)

        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestUpdate:
    @pytest.fixture
    def application_to_update(
        self,
        application_name: str,
        application_url: str,
        application_description: str,
        application_icon: str,
        application_display: bool,
    ) -> Application:
        return Application(
            name=application_name,
            url=application_url,
            description=application_description,
            icon=application_icon,
            display=application_display,
        )

    @pytest.fixture
    def updated_application(self, application_display: bool) -> ApplicationUpdate:
        return ApplicationUpdate(
            name="some new name",
            url="some new url",
            description="some new desc",
            icon="some new icon",
            display=(not application_display),
        )

    @pytest.mark.parametrize("db_get_return_val", [application_to_update])
    async def test_update_with_user_found(
        self,
        application_id: int,
        updated_application: ApplicationUpdate,
        mock_db: Mock,
        db_get_return_val: Application,
    ) -> None:
        response = await application.update_application(
            application_id=application_id,
            application=updated_application,
            db=mock_db,
        )

        mock_db.add.assert_called_once_with(db_get_return_val)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(db_get_return_val)
        assert response == db_get_return_val

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_update_with_user_not_found(
        self,
        application_id: int,
        updated_application: ApplicationUpdate,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await application.update_application(
                application_id=application_id,
                application=updated_application,
                db=mock_db,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
