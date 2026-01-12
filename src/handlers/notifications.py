async def send_vacancy_notification(context, chat_id: int, vacancy_data: dict):
    """Отправка уведомления о новой вакансии"""
    try:
        message = format_vacancy_message(vacancy_data)
        await context.bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления: {e}")


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
        "🚨 Новая вакансия!\n\n"
        f"📌 Должность: {title}\n"
        f"🏢 Компания: {company}\n"
        f"💰 Зарплата: {salary_text}\n"
        f"🔗 Ссылка: {url}\n\n"
        "Используйте /cover_letter для создания сопроводительного письма"
    )
