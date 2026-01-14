from src.core.logger import get_logger
from src.storage.database import db
from src.storage.repositories.filter_repo import filter_repo

logger = get_logger(__name__)


class FilterService:
    async def get_user_filters(self, telegram_id: int):
        async for session in db.get_session():
            return await filter_repo.get_all_filters(session, telegram_id)
        return {}

    async def save_filter(self, telegram_id: int, filter_type: str, value):
        async for session in db.get_session():
            return await filter_repo.save_filter(session, telegram_id, filter_type, value)
        return False

    async def to_hh_params(self, filters: dict) -> dict:
        """Фильтры → параметры HH API"""
        params = {}

        # Текст поиска
        search_parts = []
        if filters.get('profession'):
            search_parts.append(filters['profession'])
        if filters.get('keywords'):
            keywords = filters['keywords']
            if isinstance(keywords, list):
                search_parts.extend(keywords)
            else:
                search_parts.append(keywords)

        if search_parts:
            params['text'] = ' '.join(search_parts)

        # Регион (ID из HH API)
        area_map = {'Москва': 1, 'Санкт-Петербург': 2, 'remote': 113}
        if filters.get('area') in area_map:
            params['area'] = area_map[filters['area']]
        elif filters.get('area') and filters['area'] != 'any':
            # Если город не из списка, пока пропускаем
            pass

        # Зарплата
        if filters.get('salary_min'):
            params['salary'] = filters['salary_min']

        # Опыт
        exp_map = {
            'noExperience': 'noExperience',
            'junior': 'between1And3',
            'middle': 'between3And6',
            'senior': 'moreThan6'
        }
        if filters.get('experience') in exp_map:
            params['experience'] = exp_map[filters['experience']]

        # График работы
        schedule_map = {
            'office': 'fullDay',
            'remote': 'remote',
            'hybrid': 'flexible',
            'any': None
        }
        if filters.get('schedule') in schedule_map and schedule_map[filters['schedule']]:
            params['schedule'] = schedule_map[filters['schedule']]

        # Тип занятости
        employment_map = {
            'fullDay': 'full',
            'partDay': 'part',
            'project': 'project',
            'internship': 'probation',
            'shift': 'shift'
        }
        if filters.get('employment') in employment_map:
            params['employment'] = employment_map[filters['employment']]

        return params

    async def get_default_filters(self):
        return {'profession': 'Python', 'experience': 'junior'}


filter_service = FilterService()