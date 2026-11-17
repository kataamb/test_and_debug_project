import uuid
from typing import Optional
from abstract_repositories.iuser_repository import IUserRepository
from models.user import User

class FakeUserRepository(IUserRepository):
    def __init__(self):
        self._storage: dict[uuid.UUID, User] = {}

    async def create(self, user: User) -> User:
        self._storage[user.id] = user
        return user

    async def delete(self, profile_id: uuid.UUID) -> bool:
        if profile_id in self._storage:
            del self._storage[profile_id]
            return True
        return False

    async def find_by_email(self, email: str) -> Optional[User]:
        for user in self._storage.values():
            if user.email == email:
                return user
        return None

    async def does_exist(self, profile_id: uuid.UUID) -> bool:
        for user in self._storage.values():
            if user.id == profile_id:
                return True
        return False
