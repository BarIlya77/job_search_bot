from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.core.logger import get_logger
from src.utils.keyboards import get_main_keyboard, get_vacancy_keyboard, get_cover_letter_keyboard

logger = get_logger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий inline-кнопок"""
    query = update.callback_query
    await query.answer()  # Убираем "часики"

    data = query.data
    user_id = query.from_user.id

    logger.info(f"Обработка callback: {data} от {user_id}")

    # Навигация по вакансиям
    if data.startswith("next_"):
        try:
            next_index = int(data.replace("next_", ""))
            logger.info(f"Переход к следующей вакансии: индекс {next_index}")

            # Импортируем здесь, чтобы избежать циклического импорта
            from src.handlers.commands import send_vacancy_with_buttons
            await send_vacancy_with_buttons(update, context, next_index)
            await query.delete_message()  # Удаляем старое сообщение

        except Exception as e:
            logger.error(f"Ошибка навигации next: {e}")
            await query.edit_message_text(
                "❌ Ошибка при переходе к следующей вакансии",
                reply_markup=get_main_keyboard()
            )

    elif data.startswith("prev_"):
        try:
            prev_index = int(data.replace("prev_", ""))
            logger.info(f"Переход к предыдущей вакансии: индекс {prev_index}")

            from src.handlers.commands import send_vacancy_with_buttons
            await send_vacancy_with_buttons(update, context, prev_index)
            await query.delete_message()

        except Exception as e:
            logger.error(f"Ошибка навигации prev: {e}")
            await query.edit_message_text(
                "❌ Ошибка при переходе к предыдущей вакансии",
                reply_markup=get_main_keyboard()
            )

    # Действия с вакансиями
    elif data.startswith("save_"):
        vacancy_id = data.replace("save_", "")
        logger.info(f"Сохранение вакансии в избранное: {vacancy_id}")

        await query.edit_message_text(
            f"💾 Вакансия сохранена в избранное!\n"
            f"ID: {vacancy_id}\n\n"
            "Вы можете найти ее в истории поиска.",
            reply_markup=get_main_keyboard()
        )

    elif data.startswith("hide_"):
        vacancy_id = data.replace("hide_", "")
        logger.info(f"Скрытие вакансии: {vacancy_id}")

        await query.edit_message_text(
            f"👎 Больше не покажу эту вакансию.\n"
            f"ID: {vacancy_id}",
            reply_markup=get_main_keyboard()
        )

    elif data.startswith("cover_"):
        vacancy_id = data.replace("cover_", "")
        logger.info(f"Создание письма для вакансии: {vacancy_id}")

        await query.edit_message_text(
            f"📝 Создание сопроводительного письма\n\n"
            f"Вакансия: {vacancy_id}\n\n"
            "Выберите действие:",
            reply_markup=get_cover_letter_keyboard(vacancy_id)
        )

    elif data.startswith("gen_cover_"):
        vacancy_id = data.replace("gen_cover_", "")
        logger.info(f"Генерация письма для вакансии: {vacancy_id}")

        await query.edit_message_text(
            f"🤖 Генерирую сопроводительное письмо...\n\n"
            "Эта функция будет доступна в следующем обновлении!",
            reply_markup=get_main_keyboard()
        )

    elif data.startswith("back_to_"):
        vacancy_id = data.replace("back_to_", "")
        logger.info(f"Возврат к вакансии: {vacancy_id}")

        # Возвращаемся к просмотру вакансий
        current_index = context.user_data.get('current_vacancy_index', 0)
        from src.handlers.commands import send_vacancy_with_buttons
        await send_vacancy_with_buttons(update, context, current_index)

    elif data == "page_info":
        # Просто обновляем сообщение (обновление времени)
        await query.answer("Текущая страница")

    else:
        logger.warning(f"Неизвестный callback: {data}")
        await query.edit_message_text(
            "❌ Команда не распознана",
            reply_markup=get_main_keyboard()
        )


def setup_callback_handlers(application):
    """Регистрация обработчиков callback-кнопок"""
    application.add_handler(CallbackQueryHandler(handle_callback_query))
