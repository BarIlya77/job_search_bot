from telegram import Bot
from src.core.logger import get_logger
from src.services.hh_client import hh_client

logger = get_logger(__name__)


async def send_vacancy_notification(bot: Bot, chat_id: int, vacancy_data: dict):
    """Отправка уведомления о новой вакансии"""
    try:
        message = hh_client.format_vacancy_message(vacancy_data)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        logger.info(f"Уведомление отправлено пользователю {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления пользователю {chat_id}: {e}")


def format_vacancy_message(vacancy: dict) -> str:
    """Форматирование данных вакансии в читаемое сообщение"""
    title = vacancy.get('name', 'Без названия')
    company = vacancy.get('employer', {}).get('name', 'Не указано')
    salary = vacancy.get('salary')
    url = vacancy.get('alternate_url', 'Нет ссылки')

    salary_text = "Не указана"
    if salary:
        if salary.get('from') and salary.get('to'):
            salary_text = f"{salary['from']} - {salary['to']} {salary['currency']}"
        elif salary.get('from'):
            salary_text = f"от {salary['from']} {salary['currency']}"
        elif salary.get('to'):
            salary_text = f"до {salary['to']} {salary['currency']}"

    return (
        "🚨 *Новая вакансия!*\n\n"
        f"📌 *Должность:* {title}\n"
        f"🏢 *Компания:* {company}\n"
        f"💰 *Зарплата:* {salary_text}\n"
        f"🔗 [Ссылка на вакансию]({url})\n\n"
        "Используйте кнопки под сообщением для действий"
    )
