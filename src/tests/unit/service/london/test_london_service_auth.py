import pytest
import allure

from tests.test_data.models.mother_auth import UserMother
from core.create_jwt import JWTManager


@allure.feature("Auth Service")
@allure.story("London school unit tests")
class TestAuthServiceLondon:

    # =========================================================================
    # register()
    # =========================================================================
    @allure.story("register()")
    @allure.title("register: успешная регистрация")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_register_success_london(self, service_auth_london, mock_repo_user):
        # Arrange
        with allure.step("Подготовить пользователя и настроить моки"):
            user = UserMother.valid_user()
            reg_dict = UserMother.to_register_dict(user)
            mock_repo_user.find_by_email.return_value = None
            mock_repo_user.create.return_value = user

        # Act
        with allure.step("Вызвать service.register"):
            result = await service_auth_london.register(None, reg_dict)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == user
            mock_repo_user.find_by_email.assert_called_once_with(user.email)

    @allure.story("register()")
    @allure.title("register: email уже занят → ValueError")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_register_duplicate_email_throws_exception_london(self, service_auth_london, mock_repo_user):
        # Arrange (Класс эквивалентности: Email уже занят)
        with allure.step("Настроить мок: репозиторий находит дубликат"):
            user = UserMother.valid_user()
            reg_dict = UserMother.to_register_dict(user)
            mock_repo_user.find_by_email.return_value = user

        # Act & Assert (Тест на Exception по требованию лабы)
        with allure.step("Ожидать ValueError 'User already exists'"):
            with pytest.raises(ValueError, match="User already exists"):
                await service_auth_london.register(None, reg_dict)

    @allure.story("register()")
    @allure.title("register: пароли не совпадают → ValueError")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_register_passwords_dont_match_throws_exception_london(self, service_auth_london, mock_repo_user):
        # Arrange (Класс эквивалентности: Пароли не совпадают)
        with allure.step("Подготовить reg_dict с несовпадающими паролями"):
            user = UserMother.valid_user()
            reg_dict = UserMother.to_register_dict(user, repeat_password="different_password")
            mock_repo_user.find_by_email.return_value = None

        # Act & Assert
        with allure.step("Ожидать ValueError 'Passwords didn't matched!'"):
            with pytest.raises(ValueError, match="Passwords didn't matched!"):
                await service_auth_london.register(None, reg_dict)

    # =========================================================================
    # login()
    # =========================================================================
    @allure.story("login()")
    @allure.title("login: успешный вход, токен валиден")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_login_success_london(self, service_auth_london, mock_repo_user):
        # Arrange
        with allure.step("Настроить мок: пользователь найден"):
            user = UserMother.valid_user()
            mock_repo_user.find_by_email.return_value = user

        # Act
        with allure.step("Вызвать service.login"):
            token = await service_auth_london.login(None, user.email, user.password)

        # Assert
        with allure.step("Проверить токен и его payload"):
            assert token is not None
            payload = JWTManager.decode_token(token)
            assert payload["sub"] == user.email
            assert payload["id"] == str(user.id)

    @allure.story("login()")
    @allure.title("login: email не найден → ValueError")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_login_email_not_found_throws_exception_london(self, service_auth_london, mock_repo_user):
        # Arrange (Класс эквивалентности: Емейла нет в БД)
        with allure.step("Настроить мок: пользователь не найден"):
            mock_repo_user.find_by_email.return_value = None

        # Act & Assert
        with allure.step("Ожидать ValueError 'Invalid credentials'"):
            with pytest.raises(ValueError, match="Invalid credentials"):
                await service_auth_london.login(None, "missing@example.com", "any_password")

    @allure.story("login()")
    @allure.title("login: неверный пароль → ValueError")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_login_wrong_password_throws_exception_london(self, service_auth_london, mock_repo_user):
        # Arrange (Класс эквивалентности: Пароль неверен при верном емейле)
        with allure.step("Настроить мок: пользователь найден, пароль неверный"):
            user = UserMother.valid_user()
            mock_repo_user.find_by_email.return_value = user

        # Act & Assert
        with allure.step("Ожидать ValueError 'Invalid credentials'"):
            with pytest.raises(ValueError, match="Invalid credentials"):
                await service_auth_london.login(None, user.email, "wrong_password_123")

    # =========================================================================
    # verify_token()
    # =========================================================================
    @allure.story("verify_token()")
    @allure.title("verify_token: токен отозван → ValueError")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_token_revoked_throws_exception_london(self, service_auth_london):
        # Arrange (Класс эквивалентности: Токен лежит в использованных)
        with allure.step("Добавить токен в invalidated_tokens"):
            token = "some_token_string"
            service_auth_london.invalidated_tokens.add(token)

        # Act & Assert
        with allure.step("Ожидать ValueError 'Token revoked'"):
            with pytest.raises(ValueError, match="Token revoked"):
                service_auth_london.verify_token(token)