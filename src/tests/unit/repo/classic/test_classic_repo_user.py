import pytest
from sqlalchemy.exc import IntegrityError

from repositories.user_repository import UserRepository
from sql_builders.user_sql_builder import UserSqlBuilder

from tests.test_data.models.mother_auth import UserMother


class TestUserRepositoryUnit:
    """
    Unit тесты репозитория пользователей.

    Особенности реализации:
        * create() принимает User, но id игнорируется — БД генерирует новый.
        * create() создаёт сразу profile + customer + seller с одним UUID.
        * delete(profile_id) -> bool.
        * find_by_email(email) -> Optional[User].
    """

    @pytest.fixture
    async def repo(self, test_db_session):
        return UserRepository(
            session=test_db_session,
            builder=UserSqlBuilder(),
        )

    # =========================================================================
    # 1. create()
    # =========================================================================
    async def test_create_user_success(self, repo):
        user = UserMother.valid_user()

        created = await repo.create(user)

        assert created is not None
        assert created.email == user.email
        assert created.nickname == user.nickname

    async def test_create_user_persists_in_db(self, repo):
        user = UserMother.with_email("persist@example.com")
        created = await repo.create(user)

        found = await repo.find_by_email("persist@example.com")

        assert found is not None
        assert found.id == created.id

    async def test_create_user_with_duplicate_email_raises_integrity_error(self, repo):
        # Первый
        user1 = UserMother.with_email("dup@example.com")
        await repo.create(user1)

        # Второй: тот же email, но другой nickname (чтобы упало именно по email)
        user2 = UserMother.with_email("dup@example.com").model_copy(
            update={"nickname": "another_nick"}
        )

        with pytest.raises(IntegrityError):
            await repo.create(user2)

    async def test_create_user_with_duplicate_nickname_raises_integrity_error(self, repo):
        user1 = UserMother.with_email("first@example.com")
        await repo.create(user1)

        # Второй: тот же nickname, но другой email
        user2 = UserMother.with_email("second@example.com").model_copy(
            update={"nickname": user1.nickname}
        )

        with pytest.raises(IntegrityError):
            await repo.create(user2)

    # =========================================================================
    # 2. find_by_email()
    # =========================================================================
    async def test_find_by_email_returns_user_when_exists(self, repo):
        user = UserMother.with_email("found@example.com")
        created = await repo.create(user)

        found = await repo.find_by_email("found@example.com")

        assert found is not None
        assert found.id == created.id
        assert found.email == "found@example.com"

    async def test_find_by_email_returns_none_when_missing(self, repo):
        found = await repo.find_by_email("missing@example.com")

        assert found is None

    # =========================================================================
    # 3. delete()
    # =========================================================================
    async def test_delete_existing_user_returns_true(self, repo):
        user = UserMother.with_email("delete-me@example.com")
        created = await repo.create(user)

        result = await repo.delete(created.id)

        assert result is True
        # И реально исчез из БД:
        assert await repo.find_by_email("delete-me@example.com") is None