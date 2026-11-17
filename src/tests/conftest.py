import pytest
from unittest.mock import AsyncMock

from abstract_repositories.iadvert_repository import IAdvertRepository
from abstract_repositories.icategory_repository import ICategoryRepository
from services.advert_service import AdvertService

from tests.test_data.fake_repos.fake_repository_adverts import FakeAdvertRepository



from abstract_repositories.iuser_repository import IUserRepository
from services.auth_service import AuthService
from tests.test_data.fake_repos.fake_repository_auth import FakeUserRepository

from tests.test_data.fake_repos.fake_repository_categories import FakeCategoryRepository

from sql_builders.user_sql_builder import UserSqlBuilder


from abstract_repositories.ideal_repository import IDealRepository
from services.deal_service import DealsService
from tests.test_data.fake_repos.fake_repository_deals import FakeDealRepository



from abstract_repositories.iliked_repository import ILikedRepository
from services.liked_service import LikedService
from tests.test_data.fake_repos.fake_repository_liked import FakeLikedRepository


from sql_builders.advert_sql_builder import AdvertsSqlBuilder


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker



import os


# --- Здесь прописываем адрес вашего запущенного вручную Docker-контейнера ---
# Формат: postgresql+asyncpg://логин:пароль@хост:порт/имя_базы
#TEST_DB_URL = "postgresql+asyncpg://test:test@localhost:5438/adverts_db"

TEST_DB_URL = os.getenv(
    "TEST_DB_URL",
    "postgresql+asyncpg://postgres:1234@localhost:5438/adverts_db"
)


@pytest.fixture(scope="function")
def mock_repo_advert():
    return AsyncMock(spec=IAdvertRepository)

@pytest.fixture(scope="function")
def mock_repo_category():
    return AsyncMock(spec=ICategoryRepository)

@pytest.fixture(scope="function")
def mock_repo_user():
    return AsyncMock(spec=IUserRepository)

@pytest.fixture(scope="function")
def mock_repo_deal():
    """Создает изолированный асинхронный мок для IDealRepository"""
    return AsyncMock(spec=IDealRepository)

@pytest.fixture(scope="function")
def service_deal_london(mock_repo_deal,mock_repo_advert, mock_repo_user):
    return DealsService(repo=mock_repo_deal, repo_advert=mock_repo_advert, repo_user=mock_repo_user )

@pytest.fixture(scope="function")
def service_advert_london(mock_repo_advert, mock_repo_category: AsyncMock, mock_repo_user):
    return AdvertService(repo=mock_repo_advert, repo_category=mock_repo_category, repo_user=mock_repo_user)


@pytest.fixture(scope="function")
def service_advert_classic():
    fake_repo = FakeAdvertRepository()
    fake_repo_user = FakeUserRepository()
    fake_repo_cat = FakeCategoryRepository()
    return AdvertService(repo=fake_repo, repo_category= fake_repo_cat, repo_user = fake_repo_user )
    
@pytest.fixture(scope="function")
def advert_sql_builder():
    """Фикстура для создания чистого экземпляра AdvertsSqlBuilder"""
    return AdvertsSqlBuilder()




@pytest.fixture(scope="function")
def service_auth_london(mock_repo_user):
    return AuthService(user_repo=mock_repo_user)

@pytest.fixture(scope="function")
def service_auth_classic():
    fake_repo = FakeUserRepository()
    return AuthService(user_repo=fake_repo)




@pytest.fixture(scope="function")
def user_sql_builder():
    return UserSqlBuilder()






# =========================================================================
# Фикстуры для КЛАССИЧЕСКОГО стиля (с использованием вашего фейка)
# =========================================================================
@pytest.fixture(scope="function")
def service_deal_classic():
    """Создает DealsService, работающий с живым фейком в памяти"""
    fake_repo = FakeDealRepository()
    fake_repo_adv = FakeAdvertRepository()
    fake_repo_user = FakeUserRepository()
    return DealsService(fake_repo, fake_repo_adv, fake_repo_user)





# Лондонский стиль
@pytest.fixture(scope="function")
def mock_repo_liked():
    return AsyncMock(spec=ILikedRepository)

@pytest.fixture(scope="function")
def service_liked_london(mock_repo_liked):
    return LikedService(repo=mock_repo_liked)

# Классический стиль
@pytest.fixture(scope="function")
def service_liked_classic():
    return LikedService(repo=FakeLikedRepository())


#____________________________________________________________________________________



@pytest.fixture(scope="session")
async def test_db_engine():
    """
    Один движок на всю сессию тестов.
    Pytest-asyncio сам подставит под него сессионный event_loop согласно вашему pytest.ini.
    """
    engine = create_async_engine(TEST_DB_URL, future=True, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine):
    """
    Абсолютно изолированная сессия для каждого теста.
    Каждый тест выполняется внутри своей транзакции, которая принудительно
    откатывается (ROLLBACK). Гонка данных при параллельном запуске физически невозможна.
    """
    # Подключаемся к БД
    async with test_db_engine.connect() as connection:
        # Открываем внешнюю транзакцию
        async with connection.begin() as transaction:
            # Привязываем фабрику сессий к текущему изолированному соединению
            session_factory = async_sessionmaker(
                bind=connection,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )

            async with session_factory() as session:
                yield session

            # По окончании теста жестко откатываем все изменения обратно.
            # База данных остается идеально чистой, воркеры xdist не видят изменений друг друга.
            await transaction.rollback()



@pytest.fixture(scope="function")
def integration_advert_repo(test_db_session):
    """Предоставляет готовый реальный репозиторий, подключенный к тестовой сессии БД"""
    from repositories.advert_repository import AdvertsRepository
    from sql_builders.advert_sql_builder import AdvertsSqlBuilder
    return AdvertsRepository(session=test_db_session, builder=AdvertsSqlBuilder())



#