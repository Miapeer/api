from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from miapeer.models.miapeer import (
    Application,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)
from miapeer.routers.miapeer import application

pytestmark = pytest.mark.asyncio


raw_application_id = 12345


@pytest.fixture
def application_id() -> int:
    return raw_application_id


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


@pytest.fixture
def basic_application(
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


@pytest.fixture
def complete_application(application_id: int, basic_application: Application) -> Application:
    return Application.model_validate(basic_application.model_dump(), update={"application_id": application_id})


class TestGetAll:
    @pytest.fixture
    def multiple_applications(self, complete_application: Application) -> list[Application]:
        return [complete_application, complete_application]

    @pytest.fixture
    def expected_multiple_applications(self, complete_application: Application) -> list[ApplicationRead]:
        working_application = ApplicationRead.model_validate(complete_application)
        return [working_application, working_application]

    @pytest.fixture
    def expected_sql(self) -> str:
        return f"SELECT miapeer_application.name, miapeer_application.url, miapeer_application.description, miapeer_application.icon, miapeer_application.display, miapeer_application.application_id \nFROM miapeer_application ORDER BY miapeer_application.name ASC"

    @pytest.mark.parametrize(
        "db_all_return_val, expected_response",
        [([], []), (pytest.lazy_fixture("multiple_applications"), pytest.lazy_fixture("expected_multiple_applications"))],
    )
    async def test_get_all(self, mock_db: Mock, expected_sql: str, expected_response: list[ApplicationRead]) -> None:
        response = await application.get_all_applications(db=mock_db)

        sql = mock_db.exec.call_args.args[0]
        sql_str = str(sql.compile(compile_kwargs={"literal_binds": True}))

        assert sql_str == expected_sql
        assert response == expected_response


class TestCreate:
    def db_refresh(obj) -> None:  # type: ignore
        obj.application_id = raw_application_id

    @pytest.fixture
    def application_to_create(
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

    @pytest.mark.parametrize("db_first_return_val, db_refresh_patch_method", [("some data", db_refresh)])
    async def test_create(
        self,
        application_to_create: ApplicationCreate,
        complete_application: Application,
        mock_db: Mock,
    ) -> None:
        await application.create_application(application=application_to_create, db=mock_db)

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == complete_application.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param: Application = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == complete_application.model_dump()

        # Don't need to test the response here because it's just the updated application_to_add


class TestGet:
    @pytest.fixture
    def expected_response(self, complete_application: Application) -> ApplicationRead:
        return ApplicationRead.model_validate(complete_application)

    @pytest.mark.parametrize("db_get_return_val", [pytest.lazy_fixture("complete_application")])
    async def test_get_with_data(self, application_id: int, mock_db: Mock, expected_response: ApplicationRead) -> None:
        response = await application.get_application(application_id=application_id, db=mock_db)

        assert response == expected_response

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_get_with_no_data(self, application_id: int, mock_db: Mock) -> None:
        with pytest.raises(HTTPException):
            await application.get_application(application_id=application_id, db=mock_db)


class TestDelete:
    @pytest.mark.parametrize("db_get_return_val", ["some data", 123])
    async def test_delete_with_application_found(self, application_id: int, mock_db: Mock, db_get_return_val: Any) -> None:
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
    def application_updates(self, application_display: bool) -> ApplicationUpdate:
        return ApplicationUpdate(
            name="some new name",
            url="some new url",
            description="some new desc",
            icon="some new icon",
            display=(not application_display),
        )

    @pytest.fixture
    def updated_application(self, complete_application: Application) -> Application:
        return Application.model_validate(
            complete_application.model_dump(),
            update={
                "name": "some new name",
                "url": "some new url",
                "description": "some new desc",
                "icon": "some new icon",
                "display": (not application_display),
            },
        )

    @pytest.fixture
    def expected_response(self, updated_application: Application) -> ApplicationRead:
        return ApplicationRead.model_validate(updated_application.model_dump())

    @pytest.mark.parametrize("db_get_return_val", [pytest.lazy_fixture("complete_application")])
    async def test_update_with_user_found(
        self,
        application_id: int,
        application_updates: ApplicationUpdate,
        mock_db: Mock,
        updated_application: Application,
        expected_response: ApplicationRead,
    ) -> None:
        response = await application.update_application(
            application_id=application_id,
            application=application_updates,
            db=mock_db,
        )

        assert mock_db.add.call_count == 1
        add_call_param = mock_db.add.call_args[0][0]
        assert add_call_param.model_dump() == updated_application.model_dump()

        mock_db.commit.assert_called_once()

        assert mock_db.refresh.call_count == 1
        refresh_call_param = mock_db.refresh.call_args[0][0]
        assert refresh_call_param.model_dump() == updated_application.model_dump()

        assert response == expected_response

    @pytest.mark.parametrize("db_get_return_val", [None, []])
    async def test_update_with_user_not_found(
        self,
        application_id: int,
        application_updates: ApplicationUpdate,
        mock_db: Mock,
    ) -> None:
        with pytest.raises(HTTPException):
            await application.update_application(
                application_id=application_id,
                application=application_updates,
                db=mock_db,
            )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
