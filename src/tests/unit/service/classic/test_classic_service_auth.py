import pytest
from core.create_jwt import JWTManager
from tests.test_data.models.mother_auth import UserMother



class TestAuthServiceClassic:

    # =========================================================================
    # register()
    # =========================================================================
    async def test_register_success_classic(self, service_auth_classic):
        # Arrange
        user = UserMother.valid_user()
        reg_dict = UserMother.to_register_dict(user)

        # Act
        result = await service_auth_classic.register(None, reg_dict)

        # Assert
        assert result is not None
        assert result.email == user.email

        # Дополнительная классическая проверка: данные реально ушли в Fake-хранилище
        saved_user = await service_auth_classic.user_repo.find_by_email(
            user.email
        )
        assert saved_user == result

    async def test_register_duplicate_email_throws_exception_classic(
        self, service_auth_classic
    ):
        # Arrange (Класс эквивалентности: Email уже занят)
        user1 = UserMother.with_email("ivan@example.com")
        await service_auth_classic.user_repo.create(user1)  # Сохраняем первого

        user2 = UserMother.with_email("ivan@example.com")
        reg_dict2 = UserMother.to_register_dict(user2)  # Пробуем второго

        # Act & Assert (Тест на Exception)
        with pytest.raises(ValueError, match="User already exists"):
            await service_auth_classic.register(None, reg_dict2)

    async def test_register_passwords_dont_match_throws_exception_classic(
        self, service_auth_classic
    ):
        # Arrange (Класс эквивалентности: Пароли не совпадают)
        user = UserMother.valid_user()
        reg_dict = UserMother.to_register_dict(
            user, repeat_password="different_password"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Passwords didn't matched!"):
            await service_auth_classic.register(None, reg_dict)

    # =========================================================================
    # login()
    # =========================================================================
    async def test_login_success_classic(self, service_auth_classic):
        # Arrange
        user = UserMother.valid_user()
        await service_auth_classic.user_repo.create(user)  # Добавляем в Fake БД

        # Act
        token = await service_auth_classic.login(None, user.email, user.password)

        # Assert
        assert token is not None
        payload = JWTManager.decode_token(token)
        assert payload["sub"] == user.email
        assert payload["id"] == str(user.id)

    async def test_login_email_not_found_throws_exception_classic(
        self, service_auth_classic
    ):
        # Arrange — база фейка изначально пустая, емейла "missing@example.com" там нет

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid credentials"):
            await service_auth_classic.login(
                None, "missing@example.com", "any_password"
            )

    async def test_login_wrong_password_throws_exception_classic(
        self, service_auth_classic
    ):
        # Arrange (Класс эквивалентности: Пароль неверен при верном емейле)
        user = UserMother.valid_user()
        await service_auth_classic.user_repo.create(user)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid credentials"):
            await service_auth_classic.login(
                None, user.email, "wrong_password_123"
            )

    # =========================================================================
    # verify_token()
    # =========================================================================
    def test_verify_token_revoked_throws_exception_classic(
        self, service_auth_classic
    ):
        # Arrange (Класс эквивалентности: Токен лежит в использованных)
        token = "some_token_string"
        service_auth_classic.invalidated_tokens.add(token)

        # Act & Assert
        with pytest.raises(ValueError, match="Token revoked"):
            service_auth_classic.verify_token(token)