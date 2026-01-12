from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.storage.models import User, Vacancy, UserVacancy
from src.storage.database import db


class UserRepository:
    """Репозиторий для работы с пользователями"""

    async def get_or_create_user(self, session: AsyncSession, telegram_id: int, **kwargs):
        """Получает или создает пользователя"""
        # Ищем пользователя
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return user

        # Создаем нового
        user = User(telegram_id=telegram_id, **kwargs)
        session.add(user)
        await session.commit()
        return user

    async def update_filters(self, session: AsyncSession, telegram_id: int, filters: str):
        """Обновляет фильтры пользователя"""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(search_filters=filters)
        )
        await session.execute(stmt)
        await session.commit()


class VacancyRepository:
    """Репозиторий для работы с вакансиями"""

    async def save_vacancy(self, session: AsyncSession, vacancy_data: dict):
        """Сохраняет или обновляет вакансию"""
        vacancy = Vacancy(
            hh_id=vacancy_data['id'],
            title=vacancy_data['name'],
            employer_name=vacancy_data.get('employer', {}).get('name'),
            url=vacancy_data['alternate_url'],
            raw_data=vacancy_data
        )

        # Upsert операция (вставка или обновление)
        await session.merge(vacancy)
        await session.commit()


# Создаем экземпляры репозиториев
user_repo = UserRepository()
vacancy_repo = VacancyRepository()
