import uuid
from models.user import User

class UserBuilder:
    def __init__(self):
        self.id = uuid.uuid4()
        self.nickname = "test_user"
        self.fio = "Иванов Иван Иванович"
        self.email = "ivan@example.com"
        self.phone_number = "+79991112233"
        self.password = "secure_password123"

    def with_id(self, user_id: uuid.UUID):
        self.id = user_id
        return self

    def with_email(self, email: str):
        self.email = email
        return self

    def with_password(self, password: str):
        self.password = password
        return self

    def with_nickname(self, nickname: str):
        self.nickname= nickname
        return self

    def build(self) -> User:
        return User(
            id=self.id,
            nickname=self.nickname,
            fio=self.fio,
            email=self.email,
            phone_number=self.phone_number,
            password=self.password
        )
