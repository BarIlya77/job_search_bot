from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.storage.models import User
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """Репозиторий для работы с пользователями"""

    async def get_or_create(self, session: AsyncSession, telegram_id: int, **kwargs) -> User:
        """Получить или создать пользователя"""
        try:
            # Ищем пользователя
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                logger.info(f"Пользователь {telegram_id} найден")
                return user

            # Создаем нового
            user = User(telegram_id=telegram_id, **kwargs)
            session.add(user)
            await session.commit()
            await session.refresh(user)  # Получаем данные из БД

            logger.info(f"Создан новый пользователь: {telegram_id}")
            return user

        except Exception as e:
            logger.error(f"Ошибка в get_or_create: {e}")
            await session.rollback()
            raise

    async def update_filters(self, session: AsyncSession, telegram_id: int, filters: str) -> bool:
        """Обновить фильтры поиска пользователя"""
        try:
            stmt = (
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(search_filters=filters)
            )
            result = await session.execute(stmt)
            await session.commit()

            updated = result.rowcount > 0
            if updated:
                logger.info(f"Обновлены фильтры для {telegram_id}: {filters}")

            return updated

        except Exception as e:
            logger.error(f"Ошибка обновления фильтров: {e}")
            await session.rollback()
            return False

    async def get_user(self, session: AsyncSession, telegram_id: int) -> User | None:
        """Получить пользователя по ID"""
        try:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

    async def get_active_users(self, session: AsyncSession):
        """Получить всех активных пользователей"""
        try:
            stmt = select(User).where(User.is_active == True)
            result = await session.execute(stmt)
            users = result.scalars().all()
            logger.info(f"Найдено {len(users)} активных пользователей")
            return users
        except Exception as e:
            logger.error(f"Ошибка получения активных пользователей: {e}")
            return []


# Создаем глобальный экземпляр
user_repo = UserRepository()
