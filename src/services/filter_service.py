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
        if filters.get('profession'):
            params['text'] = filters['profession']
            if filters.get('experience'):
                params['text'] += f" {filters['experience']}"

        # Регион (ID из HH API)
        area_map = {'Москва': 1, 'Санкт-Петербург': 2, 'remote': 113}
        if filters.get('area') in area_map:
            params['area'] = area_map[filters['area']]

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

        return params

    async def get_default_filters(self):
        return {'profession': 'Python', 'experience': 'junior'}


filter_service = FilterService()
