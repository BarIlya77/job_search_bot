from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from src.utils.keyboards import get_main_keyboard, get_filters_keyboard, get_search_keyboard
from src.core.logger import get_logger


logger = get_logger(__name__)


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки Reply Keyboard"""
    text = update.message.text
    user_id = update.effective_user.id

    logger.info(f"Получено сообщение: {text} от {user_id}")

    # Импортируем здесь, чтобы избежать циклических импортов
    from src.handlers.commands import (
        search_command, set_filters_command,
        my_filters_command, status_command,
        help_command, stop_command
    )

    if text == "🔍 Поиск вакансий":
        await update.message.reply_text(
            "Выберите тип поиска:",
            reply_markup=get_search_keyboard()
        )

    elif text == "🔎 Искать сейчас":
        await search_command(update, context)

    # elif text == "⚙️ Мои фильтры":
    #     await update.message.reply_text(
    #         "Управление фильтрами поиска:",
    #         reply_markup=get_filters_keyboard()
    #     )
    elif text == "⚙️ Мои фильтры":
        from src.utils.filter_keyboards import get_filters_main_keyboard
        from src.storage.database import db
        from src.storage.repositories.filter_repo import filter_repo

        # Получаем текущие фильтры
        current_filters = {}
        async for session in db.get_session():
            current_filters = await filter_repo.get_all_filters(session, user_id)

        # Показываем меню фильтров
        await update.message.reply_text(
            "⚙️ *Настройка фильтров поиска*\n\n"
            "Выберите параметр для настройки:\n\n"
            f"*Текущие настройки:*\n"
            f"💼 Профессия: {current_filters.get('profession', 'не задано')}\n"
            f"💰 Зарплата от: {current_filters.get('salary_min', 'не задано')}\n"
            f"🎓 Опыт: {current_filters.get('experience', 'не задано')}\n"
            f"📍 Формат: {current_filters.get('schedule', 'не задано')}\n"
            f"🏢 Занятость: {current_filters.get('employment', 'не задано')}\n"
            f"🌍 Город: {current_filters.get('area', 'не задано')}",
            parse_mode='Markdown',
            reply_markup=get_filters_main_keyboard(current_filters)
        )


    elif text == "📝 Установить фильтры":
        await update.message.reply_text(
            "Отправьте фильтры поиска одним сообщением.\n\n"
            "Примеры:\n"
            "• `python junior москва`\n"
            "• `data scientist remote 150000`\n"
            "• `backend разработчик`",
            parse_mode='Markdown'
        )

    elif text == "👀 Показать фильтры":
        await my_filters_command(update, context)

    elif text == "🧹 Очистить фильтры":
        # Просто сохраняем пустые фильтры
        from src.storage.database import db
        from src.storage.repositories.user_repo import user_repo

        async for session in db.get_session():
            await user_repo.update_filters(session, user_id, "")

        await update.message.reply_text(
            "✅ Фильтры очищены!\n"
            "Используйте '📝 Установить фильтры' для настройки.",
            reply_markup=get_main_keyboard()
        )

    elif text == "🔙 Назад в меню" or text == "🔙 Назад":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_keyboard()
        )

    elif text == "📊 Мой статус":
        await status_command(update, context)

    elif text == "🆘 Помощь":
        await help_command(update, context)

    elif text == "⏸️ Остановить":
        await stop_command(update, context)
        await update.message.reply_text(
            "⏸️ Уведомления приостановлены",
            reply_markup=get_main_keyboard()
        )

    elif text == "▶️ Возобновить":
        # TODO: Реализовать возобновление уведомлений
        await update.message.reply_text(
            "▶️ Уведомления возобновлены!",
            reply_markup=get_main_keyboard()
        )

    elif text == "📋 История поиска":
        await update.message.reply_text(
            "📋 Ваша история поиска будет здесь...\n"
            "(функция в разработке)",
            reply_markup=get_main_keyboard()
        )

    elif text == "⏰ Автопоиск":
        await update.message.reply_text(
            "⏰ Настройка автоматического поиска...\n"
            "(функция в разработке)",
            reply_markup=get_main_keyboard()
        )

    else:
        # Если текст не команда, пробуем сохранить как фильтры
        try:
            from src.storage.database import db
            from src.storage.repositories.user_repo import user_repo

            async for session in db.get_session():
                success = await user_repo.update_filters(session, user_id, text)

            if success:
                await update.message.reply_text(
                    f"✅ Фильтры сохранены: `{text}`\n\n"
                    "Используйте '🔍 Поиск вакансий' для поиска",
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка сохранения. Используйте /start",
                    reply_markup=get_main_keyboard()
                )
        except Exception as e:
            logger.error(f"Ошибка обработки текста: {e}")
            await update.message.reply_text(
                "Не понимаю команду. Используйте кнопки меню.",
                reply_markup=get_main_keyboard()
            )


def setup_message_handlers(application):
    """Регистрация обработчиков сообщений"""
    # Обрабатываем все текстовые сообщения, кроме команд
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages)
    )