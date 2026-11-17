import uuid
import pytest
import allure

from core.create_jwt import JWTManager
from services.auth_service import AuthService
from repositories.user_repository import UserRepository
from sql_builders.user_sql_builder import UserSqlBuilder
from tests.test_data.models.mother_auth import UserMother


@allure.feature("Integration Tests")
@allure.story("AuthService + PostgreSQL")
class TestAuthServiceIntegration:
    """
    Интеграционные тесты: AuthService + UserRepository + PostgreSQL.
    Использует только существующую фикстуру test_db_session.
    """

    @pytest.fixture
    def auth_service(self, test_db_session):
        user_repo = UserRepository(test_db_session, UserSqlBuilder())
        return AuthService(user_repo=user_repo)

    @allure.title("Интеграция: успешная регистрация пользователя и сохранение в БД")
    async def test_register_user_persists_in_db(self, auth_service, test_db_session):
        # Arrange
        suffix = uuid.uuid4().hex[:8]
        user = (
            UserMother.with_email(f"reg_{suffix}@example.com")
            .model_copy(update={"nickname": f"reg_user_{suffix}"})
        )
        reg_dict = UserMother.to_register_dict(user)

        # Act
        created = await auth_service.register(test_db_session, reg_dict)

        # Assert
        assert created is not None
        assert created.email == user.email
        assert await auth_service.user_repo.does_exist(created.id) is True

        found = await auth_service.user_repo.find_by_email(user.email)
        assert found is not None
        assert found.id == created.id

    @allure.title("Интеграция: повторная регистрация с тем же email -> ValueError")
    async def test_register_duplicate_email_raises_error(self, auth_service, test_db_session):
        # Arrange
        suffix = uuid.uuid4().hex[:8]
        email = f"dup_{suffix}@example.com"
        user1 = UserMother.with_email(email).model_copy(update={"nickname": f"u1_{suffix}"})
        await auth_service.register(test_db_session, UserMother.to_register_dict(user1))

        user2 = UserMother.with_email(email).model_copy(update={"nickname": f"u2_{suffix}"})

        # Act & Assert
        with pytest.raises(ValueError, match="User already exists"):
            await auth_service.register(test_db_session, UserMother.to_register_dict(user2))

    @allure.title("Интеграция: регистрация с несовпадающими паролями -> ValueError")
    async def test_register_password_mismatch_raises_error(self, auth_service, test_db_session):
        # Arrange
        suffix = uuid.uuid4().hex[:8]
        email = f"mismatch_{suffix}@example.com"
        user = UserMother.with_email(email).model_copy(update={"nickname": f"mm_{suffix}"})
        reg_dict = UserMother.to_register_dict(user, repeat_password="wrong_password")

        # Act & Assert
        with pytest.raises(ValueError, match="Passwords didn't matched!"):
            await auth_service.register(test_db_session, reg_dict)

        assert await auth_service.user_repo.find_by_email(email) is None

    @allure.title("Интеграция: успешный логин по данным из БД и декодирование JWT")
    async def test_login_success_returns_valid_jwt(self, auth_service, test_db_session):
        # Arrange
        suffix = uuid.uuid4().hex[:8]
        user = (
            UserMother.with_email(f"login_{suffix}@example.com")
            .model_copy(update={"nickname": f"login_{suffix}", "password": "MySecretPassword1"})
        )
        created = await auth_service.register(test_db_session, UserMother.to_register_dict(user))

        # Act
        token = await auth_service.login(test_db_session, user.email, "MySecretPassword1")

        # Assert
        assert token
        payload = JWTManager.decode_token(token)
        assert payload["sub"] == user.email
        assert payload["id"] == str(created.id)
        assert payload["role"] == "authorized_user"

    @allure.title("Интеграция: логин с неверным паролем -> ValueError")
    async def test_login_wrong_password_raises_error(self, auth_service, test_db_session):
        # Arrange
        suffix = uuid.uuid4().hex[:8]
        user = UserMother.with_email(f"badpass_{suffix}@example.com").model_copy(
            update={"nickname": f"bp_{suffix}"}
        )
        await auth_service.register(test_db_session, UserMother.to_register_dict(user))

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid credentials"):
            await auth_service.login(test_db_session, user.email, "definitely_wrong_pass")

    @allure.title("Интеграция: отзыв токена (logout) и проверка verify_token")
    async def test_logout_revokes_token(self, auth_service, test_db_session):
        # Arrange
        suffix = uuid.uuid4().hex[:8]
        user = UserMother.with_email(f"logout_{suffix}@example.com").model_copy(
            update={"nickname": f"lo_{suffix}"}
        )
        await auth_service.register(test_db_session, UserMother.to_register_dict(user))
        token = await auth_service.login(test_db_session, user.email, user.password)

        # Act
        logged_out = await auth_service.logout(token)

        # Assert
        assert logged_out is True
        with pytest.raises(ValueError, match="Token revoked"):
            auth_service.verify_token(token)