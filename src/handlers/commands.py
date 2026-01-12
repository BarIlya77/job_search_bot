from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from src.core.logger import get_logger
from src.utils.keyboards import get_main_keyboard
from src.storage.database import db
from src.storage.repositories.user_repo import user_repo
from src.storage.repositories.vacancy_repo import vacancy_repo
from src.storage.repositories.filter_repo import filter_repo
from src.services.hh_client import hh_client

logger = get_logger(__name__)


def build_hh_query(structured_filters: dict) -> str:
    """
    Преобразует структурированные фильтры в строку для API HH.ru
    """
    if not structured_filters:
        return "python junior"

    parts = []

    # Профессия
    if structured_filters.get('profession'):
        parts.append(structured_filters['profession'])

    # Опыт
    experience_map = {
        'noExperience': 'без опыта',
        'junior': 'junior',
        'middle': 'middle',
        'senior': 'senior',
        'lead': 'lead'
    }
    if structured_filters.get('experience'):
        exp = structured_filters['experience']
        parts.append(experience_map.get(exp, exp))

    # Город
    if structured_filters.get('area') and structured_filters['area'] not in ['any', 'remote']:
        parts.append(structured_filters['area'])

    # Ключевые слова
    if structured_filters.get('keywords'):
        if isinstance(structured_filters['keywords'], list):
            parts.extend(structured_filters['keywords'])
        else:
            parts.append(structured_filters['keywords'])

    # Формат работы
    if structured_filters.get('schedule') == 'remote':
        parts.append('удаленно')

    return ' '.join(parts) if parts else "python junior"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с клавиатурой"""
    user = update.effective_user

    # Регистрируем пользователя
    async for session in db.get_session():
        db_user = await user_repo.get_or_create(
            session,
            telegram_id=user.id,
            first_name=user.first_name,
            username=user.username
        )

    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — бот для поиска работы на HH.ru.\n"
        "Используй кнопки ниже для управления:\n\n"
        "• 🔍 **Поиск вакансий** — найти новые вакансии\n"
        "• ⚙️ **Мои фильтры** — настроить параметры поиска\n"
        "• 📊 **Мой статус** — текущие настройки\n"
        "• 🆘 **Помощь** — список всех команд"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск вакансий с inline-клавиатурами"""
    user_id = update.effective_user.id

    await update.message.reply_text(
        "🔍 Начинаю поиск вакансий...",
        reply_markup=get_main_keyboard()
    )

    # Получаем фильтры
    search_text = "python junior"  # По умолчанию

    async for session in db.get_session():
        # Пробуем получить из новой системы фильтров
        structured_filters = await filter_repo.get_all_filters(session, user_id)

        if structured_filters:
            search_text = build_hh_query(structured_filters)
            logger.info(f"Использую структурированные фильтры: {search_text}")
        else:
            # Пробуем из старой системы
            user = await user_repo.get_user(session, user_id)
            if user and user.search_filters:
                search_text = user.search_filters
                logger.info(f"Использую старые фильтры: {search_text}")

    logger.info(f"Поиск вакансий по: {search_text}")

    # Ищем вакансии
    try:
        vacancies = await hh_client.search_vacancies(search_text, per_page=5)

        if not vacancies:
            await update.message.reply_text(
                "😔 По вашему запросу ничего не найдено",
                reply_markup=get_main_keyboard()
            )
            return

        await update.message.reply_text(f"📊 Найдено вакансий: {len(vacancies)}")

        # Сохраняем вакансии в контексте для навигации
        context.user_data['search_results'] = vacancies
        context.user_data['current_vacancy_index'] = 0

        # Отправляем первую вакансию
        await send_vacancy_with_buttons(update, context, 0)

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при поиске вакансий",
            reply_markup=get_main_keyboard()
        )


async def send_vacancy_with_buttons(update, context, index: int):
    """Отправка одной вакансии с inline-кнопками"""
    from src.utils.keyboards import get_vacancy_keyboard

    vacancies = context.user_data.get('search_results', [])

    if index >= len(vacancies):
        await update.message.reply_text(
            "✅ Это все найденные вакансии!",
            reply_markup=get_main_keyboard()
        )
        return

    vacancy_data = vacancies[index]
    vacancy_id = vacancy_data.get('id', '')

    try:
        # Сохраняем в БД
        async for session in db.get_session():
            vacancy = await vacancy_repo.save_vacancy(session, vacancy_data)
            await vacancy_repo.mark_as_notified(session, update.effective_user.id, vacancy_id)

        logger.info(f"Отправка вакансии {index + 1}/{len(vacancies)}: {vacancy_id}")

        # Форматируем сообщение
        message = hh_client.format_vacancy_message(vacancy_data)

        # Создаем inline-клавиатуру
        keyboard = get_vacancy_keyboard(
            vacancy_id=vacancy_id,
            page=index,
            total=len(vacancies)
        )

        # Отправляем с кнопками
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

        # Обновляем индекс
        context.user_data['current_vacancy_index'] = index

    except Exception as e:
        logger.error(f"Ошибка отправки вакансии: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ Ошибка при обработке вакансии",
            reply_markup=get_main_keyboard()
        )


async def set_filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_filters"""
    if not context.args:
        await update.message.reply_text(
            "Укажите критерии поиска через пробел.\n\n"
            "📋 Примеры:\n"
            "/set_filters python junior\n"
            "/set_filters python django backend\n"
            "/set_filters data scientist remote\n\n"
            "💡 Советы:\n"
            "• Используйте ключевые слова\n"
            "• Указывайте уровень (junior, middle, senior)\n"
            "• Добавьте город или 'remote'"
        )
        return

    filters = ' '.join(context.args)
    user_id = update.effective_user.id

    # Сохраняем фильтры в базу данных (старая система для совместимости)
    async for session in db.get_session():
        success = await user_repo.update_filters(session, user_id, filters)

    if success:
        await update.message.reply_text(
            f"✅ Фильтры сохранены:\n`{filters}`\n\n"
            "📊 Теперь бот будет искать вакансии по этим критериям.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Сохранены фильтры для {user_id}: {filters}")
    else:
        await update.message.reply_text(
            "❌ Ошибка сохранения. Попробуйте позже или используйте /start",
            reply_markup=get_main_keyboard()
        )


async def my_filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /my_filters"""
    user_id = update.effective_user.id
    filters_text = "❌ У вас еще не заданы фильтры поиска."

    async for session in db.get_session():
        user = await user_repo.get_user(session, user_id)
        if user and user.search_filters:
            filters_text = f"🔍 Ваши текущие фильтры:\n\n`{user.search_filters}`"

    await update.message.reply_text(
        filters_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    user_id = update.effective_user.id

    async for session in db.get_session():
        user = await user_repo.get_user(session, user_id)

    if user:
        status = (
            "📊 Ваш статус:\n\n"
            f"• 👤 Имя: {user.first_name}\n"
            f"• 🔍 Фильтры: {user.search_filters or 'не заданы'}\n"
            f"• 📅 Зарегистрирован: {user.created_at.strftime('%d.%m.%Y')}\n"
            f"• 🟢 Активен: {'да' if user.is_active else 'нет'}"
        )
    else:
        status = "❌ Вы не зарегистрированы. Используйте /start"

    await update.message.reply_text(
        status,
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📋 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/set_filters - Настроить фильтры поиска\n"
        "/my_filters - Показать текущие фильтры\n"
        "/status - Показать статус\n"
        "/stop - Остановить уведомления\n"
        "/search - Найти вакансии\n\n"
        "⚙️ Пример настройки:\n"
        "/set_filters <ключевые слова> [город] [з/п] [опыт]"
    )
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_keyboard()
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stop"""
    await update.message.reply_text(
        "⏸️ Уведомления приостановлены.\n"
        "Используйте /start для возобновления.",
        reply_markup=get_main_keyboard()
    )


def setup_handlers(application):
    """Регистрация всех обработчиков команд"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_filters", set_filters_command))
    application.add_handler(CommandHandler("my_filters", my_filters_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("search", search_command))
