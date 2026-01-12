from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from src.utils.config import load_config
from src.storage.models import Base
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.config = load_config()
        self.engine = None
        self.async_session = None

    async def connect(self):
        """Создает engine и сессию для работы с БД"""
        # Формируем URL подключения
        db_config = self.config.db_config
        database_url = (
            f"postgresql+asyncpg://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        # Создаем engine (движок БД)
        self.engine = create_async_engine(
            database_url,
            echo=False,  # True для отладки SQL запросов
            pool_size=10,
            max_overflow=20
        )

        # Создаем фабрику сессий
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        logger.info("✅ Engine SQLAlchemy создан")

    async def create_tables(self):
        """Создает все таблицы в БД"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Таблицы созданы")

    async def get_session(self):
        """Возвращает сессию для работы с БД"""
        async with self.async_session() as session:
            yield session


# Глобальный экземпляр БД
db = Database()
