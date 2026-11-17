from tests.test_data.models.builder_auth import UserBuilder
from models.user import User

class UserMother:
    @staticmethod
    def valid_user() -> User:
        return UserBuilder().build()

    @staticmethod
    def with_email(email: str) -> User:
        return UserBuilder().with_email(email).build()

    @staticmethod
    def with_password(password: str) -> User:
        return UserBuilder().with_password(password).build()

    @staticmethod
    def with_nickname(nickname: str) -> User:
        return UserBuilder().with_nickname(nickname).build()

    @staticmethod
    def to_register_dict(user: User, repeat_password: str = '') -> dict:
        """Превращает объект User в словарь для метода register сервиса"""
        user_dict = user.model_dump()
        user_dict["id"] = str(user.id)
        user_dict["repeat_password"] = repeat_password or user.password
        return user_dict
