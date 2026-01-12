from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from src.storage.models import Vacancy, UserVacancy
import logging

logger = logging.getLogger(__name__)


class VacancyRepository:
    """Репозиторий для работы с вакансиями"""

    async def save_vacancy(self, session: AsyncSession, hh_data: dict) -> Vacancy:
        """Упрощенный метод сохранения - безопасная обработка"""
        try:
            # Безопасно получаем все данные
            vacancy_id = str(hh_data.get('id', ''))
            title = hh_data.get('name', 'Без названия')

            # Безопасно получаем employer
            employer = hh_data.get('employer', {})
            employer_name = employer.get('name', '') if isinstance(employer, dict) else str(employer)

            # Безопасно обрабатываем salary (может быть None)
            salary = hh_data.get('salary')
            salary_from = salary.get('from') if salary and isinstance(salary, dict) else None
            salary_to = salary.get('to') if salary and isinstance(salary, dict) else None
            salary_currency = salary.get('currency') if salary and isinstance(salary, dict) else None

            # Безопасно получаем остальные поля
            area_data = hh_data.get('area', {})
            area = area_data.get('name', '') if isinstance(area_data, dict) else str(area_data)

            exp_data = hh_data.get('experience', {})
            experience = exp_data.get('name', '') if isinstance(exp_data, dict) else str(exp_data)

            schedule_data = hh_data.get('schedule', {})
            schedule = schedule_data.get('name', '') if isinstance(schedule_data, dict) else str(schedule_data)

            url = hh_data.get('alternate_url', '')

            vacancy = Vacancy(
                hh_id=vacancy_id,
                title=title[:500],  # Ограничиваем длину для БД
                employer_name=employer_name[:500],
                salary_from=salary_from,
                salary_to=salary_to,
                salary_currency=salary_currency,
                area=area[:100],
                experience=experience[:50],
                schedule=schedule[:50],
                url=url[:500],
                raw_data=hh_data,
                published_at=None,  # Пока не сохраняем
                fetched_at=datetime.now()
            )

            # Добавляем или обновляем
            await session.merge(vacancy)
            await session.commit()
            logger.info(f"✅ Сохранена вакансия: {vacancy_id} - {title[:30]}...")
            return vacancy

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения вакансии: {e}")
            await session.rollback()
            raise

    # async def save_vacancy(self, session: AsyncSession, hh_data: dict) -> Vacancy:
    #     """Сохранить вакансию из HH.ru"""
    #     try:
    #         # Парсим данные
    #         salary = hh_data.get('salary')
    #
    #         vacancy = Vacancy(
    #             hh_id=str(hh_data['id']),
    #             title=hh_data.get('name', ''),
    #             employer_name=hh_data.get('employer', {}).get('name', ''),
    #             salary_from=salary.get('from') if salary else None,
    #             salary_to=salary.get('to') if salary else None,
    #             salary_currency=salary.get('currency') if salary else None,
    #             area=hh_data.get('area', {}).get('name', ''),
    #             experience=hh_data.get('experience', {}).get('name', ''),
    #             schedule=hh_data.get('schedule', {}).get('name', ''),
    #             url=hh_data.get('alternate_url', ''),
    #             raw_data=hh_data,
    #             published_at=datetime.fromisoformat(hh_data['published_at'].replace('Z', '+00:00')) if hh_data.get(
    #                 'published_at') else None,
    #             fetched_at=datetime.now()
    #         )
    #
    #         # Добавляем или обновляем
    #         await session.merge(vacancy)
    #         await session.commit()
    #
    #         logger.debug(f"Сохранена вакансия: {vacancy.hh_id}")
    #         return vacancy
    #
    #     except Exception as e:
    #         logger.error(f"Ошибка сохранения вакансии {hh_data.get('id')}: {e}")
    #         await session.rollback()
    #         raise

    async def mark_as_notified(self, session: AsyncSession, user_id: int, vacancy_id: str):
        """Отметить вакансию как отправленную пользователю"""
        try:
            # Проверяем, есть ли уже запись
            stmt = select(UserVacancy).where(
                and_(
                    UserVacancy.user_id == user_id,
                    UserVacancy.vacancy_id == vacancy_id
                )
            )
            result = await session.execute(stmt)
            user_vacancy = result.scalar_one_or_none()

            if user_vacancy:
                # Обновляем
                user_vacancy.notified = True
            else:
                # Создаем новую
                user_vacancy = UserVacancy(
                    user_id=user_id,
                    vacancy_id=vacancy_id,
                    notified=True
                )
                session.add(user_vacancy)

            await session.commit()
            logger.debug(f"Вакансия {vacancy_id} отмечена как отправленная для {user_id}")

        except Exception as e:
            logger.error(f"Ошибка отметки вакансии: {e}")
            await session.rollback()

    async def get_new_vacancies_for_user(self, session: AsyncSession, user_id: int, filters: str = None,
                                         limit: int = 10):
        """Получить новые вакансии для пользователя"""
        try:
            # Вакансии, которые еще не отправлялись пользователю
            subquery = select(UserVacancy.vacancy_id).where(UserVacancy.user_id == user_id)

            # Базовый запрос
            stmt = select(Vacancy).where(
                Vacancy.hh_id.not_in(subquery)
            )

            # Фильтруем по ключевым словам если есть
            if filters:
                # Простой фильтр по названию
                stmt = stmt.where(Vacancy.title.ilike(f"%{filters}%"))

            # Сортируем по дате публикации
            stmt = stmt.order_by(Vacancy.published_at.desc()).limit(limit)

            result = await session.execute(stmt)
            vacancies = result.scalars().all()

            logger.info(f"Найдено {len(vacancies)} новых вакансий для {user_id}")
            return vacancies

        except Exception as e:
            logger.error(f"Ошибка поиска вакансий: {e}")
            return []


# Глобальный экземпляр
vacancy_repo = VacancyRepository()
