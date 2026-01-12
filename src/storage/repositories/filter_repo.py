from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from src.storage.models import UserFilter
from src.core.logger import get_logger
import json

logger = get_logger(__name__)


class FilterRepository:
    """Репозиторий для работы с фильтрами пользователей"""

    async def save_filter(self, session: AsyncSession, telegram_id: int,
                          filter_name: str, filter_value) -> bool:
        """Сохранить или обновить фильтр пользователя"""
        try:
            # Проверяем, существует ли уже такой фильтр
            stmt = select(UserFilter).where(
                UserFilter.telegram_id == telegram_id,
                UserFilter.filter_name == filter_name
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Обновляем существующий
                existing.filter_value = filter_value
            else:
                # Создаем новый
                filter_obj = UserFilter(
                    telegram_id=telegram_id,
                    filter_name=filter_name,
                    filter_value=filter_value
                )
                session.add(filter_obj)

            await session.commit()
            logger.info(f"Сохранен фильтр {filter_name} для {telegram_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка сохранения фильтра: {e}")
            await session.rollback()
            return False

    async def get_filter(self, session: AsyncSession, telegram_id: int,
                         filter_name: str):
        """Получить значение фильтра"""
        stmt = select(UserFilter).where(
            UserFilter.telegram_id == telegram_id,
            UserFilter.filter_name == filter_name
        )
        result = await session.execute(stmt)
        filter_obj = result.scalar_one_or_none()

        return filter_obj.filter_value if filter_obj else None

    async def get_all_filters(self, session: AsyncSession, telegram_id: int) -> dict:
        """Получить все фильтры пользователя в виде словаря"""
        stmt = select(UserFilter).where(UserFilter.telegram_id == telegram_id)
        result = await session.execute(stmt)
        filters = result.scalars().all()

        return {f.filter_name: f.filter_value for f in filters}

    async def delete_filter(self, session: AsyncSession, telegram_id: int,
                            filter_name: str) -> bool:
        """Удалить фильтр"""
        try:
            stmt = delete(UserFilter).where(
                UserFilter.telegram_id == telegram_id,
                UserFilter.filter_name == filter_name
            )
            await session.execute(stmt)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления фильтра: {e}")
            return False

    async def clear_all_filters(self, session: AsyncSession, telegram_id: int) -> bool:
        """Очистить все фильтры пользователя"""
        try:
            stmt = delete(UserFilter).where(UserFilter.telegram_id == telegram_id)
            await session.execute(stmt)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки фильтров: {e}")
            return False


# Глобальный экземпляр
filter_repo = FilterRepository()
