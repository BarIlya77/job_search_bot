import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HHAPIClient:
    """Клиент для работы с API HeadHunter"""

    BASE_URL = "https://api.hh.ru"

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_vacancies(self, text: str, **params) -> List[Dict]:
        """Поиск вакансий по параметрам"""
        default_params = {
            "text": text,
            "area": 1,  # Москва
            "per_page": 50,  # Количество результатов
            "page": 0,  # Страница
            "order_by": "publication_time",
            "search_field": "name",  # Искать в названии
        }
        default_params.update(params)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.BASE_URL}/vacancies",
                        params=default_params,
                        headers={"User-Agent": "JobSearchBot/1.0"}
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        vacancies = data.get("items", [])
                        logger.info(f"Найдено вакансий: {len(vacancies)}")
                        return vacancies
                    else:
                        logger.error(f"Ошибка API: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Ошибка запроса к API: {e}")
            return []

    async def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """Получить детальную информацию о вакансии"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.BASE_URL}/vacancies/{vacancy_id}",
                        headers={"User-Agent": "JobSearchBot/1.0"}
                ) as response:

                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Вакансия {vacancy_id} не найдена: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Ошибка получения вакансии {vacancy_id}: {e}")
            return None

    def format_vacancy_message(self, vacancy: Dict) -> str:
        """Форматирование вакансии в читаемое сообщение"""
        title = vacancy.get('name', 'Без названия')
        employer = vacancy.get('employer', {}).get('name', 'Не указано')
        salary = vacancy.get('salary')
        area = vacancy.get('area', {}).get('name', 'Не указано')
        experience = vacancy.get('experience', {}).get('name', 'Не указан')
        url = vacancy.get('alternate_url', '')

        # Форматируем зарплату
        salary_text = "Не указана"
        if salary:
            from_salary = salary.get('from')
            to_salary = salary.get('to')
            currency = salary.get('currency', '')

            if from_salary and to_salary:
                salary_text = f"{from_salary:,} - {to_salary:,} {currency}".replace(',', ' ')
            elif from_salary:
                salary_text = f"от {from_salary:,} {currency}".replace(',', ' ')
            elif to_salary:
                salary_text = f"до {to_salary:,} {currency}".replace(',', ' ')

        # Форматируем сообщение
        message = (
            "🚨 *Новая вакансия!*\n\n"
            f"*{title}*\n"
            f"🏢 *Компания:* {employer}\n"
            f"💰 *Зарплата:* {salary_text}\n"
            f"📍 *Местоположение:* {area}\n"
            f"📊 *Опыт:* {experience}\n\n"
            f"[Ссылка на вакансию]({url})"
        )

        return message


# Синглтон
hh_client = HHAPIClient()
