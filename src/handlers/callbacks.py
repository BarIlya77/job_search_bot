from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.core.logger import get_logger
from src.utils.keyboards import get_main_keyboard, get_vacancy_keyboard, get_cover_letter_keyboard
from src.services.hh_client import hh_client
from src.storage.database import db
from src.storage.repositories.vacancy_repo import vacancy_repo

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

            # Получаем вакансии из контекста
            vacancies = context.user_data.get('search_results', [])

            if not vacancies:
                await query.edit_message_text(
                    "❌ Нет данных о вакансиях. Начните поиск заново.",
                    reply_markup=get_main_keyboard()
                )
                return

            if next_index >= len(vacancies):
                await query.edit_message_text(
                    "✅ Это последняя вакансия в списке!",
                    reply_markup=get_vacancy_keyboard(
                        vacancies[-1].get('id', ''),
                        len(vacancies) - 1,
                        len(vacancies)
                    )
                )
                return

            # Отправляем следующую вакансию
            await send_vacancy_message(update, context, next_index, query)

        except Exception as e:
            logger.error(f"Ошибка навигации next: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Ошибка при переходе к следующей вакансии",
                reply_markup=get_main_keyboard()
            )

    elif data.startswith("prev_"):
        try:
            prev_index = int(data.replace("prev_", ""))
            logger.info(f"Переход к предыдущей вакансии: индекс {prev_index}")

            vacancies = context.user_data.get('search_results', [])

            if not vacancies:
                await query.edit_message_text(
                    "❌ Нет данных о вакансиях. Начните поиск заново.",
                    reply_markup=get_main_keyboard()
                )
                return

            if prev_index < 0:
                await query.edit_message_text(
                    "✅ Это первая вакансия в списке!",
                    reply_markup=get_vacancy_keyboard(
                        vacancies[0].get('id', ''),
                        0,
                        len(vacancies)
                    )
                )
                return

            # Отправляем предыдущую вакансию
            await send_vacancy_message(update, context, prev_index, query)

        except Exception as e:
            logger.error(f"Ошибка навигации prev: {e}", exc_info=True)
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

        # Здесь можно добавить логику скрытия вакансии
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

        # Находим индекс вакансии в списке
        vacancies = context.user_data.get('search_results', [])
        index = 0
        for i, v in enumerate(vacancies):
            if v.get('id') == vacancy_id:
                index = i
                break

        await send_vacancy_message(update, context, index, query)

    elif data == "page_info":
        # Просто обновляем всплывающее сообщение
        await query.answer("Текущая страница", show_alert=False)

    elif data == "ignore_":
        vacancy_id = data.replace("ignore_", "")
        logger.info(f"Игнорирование вакансии: {vacancy_id}")

        await query.edit_message_text(
            f"❌ Вакансия скрыта.\n"
            f"ID: {vacancy_id}",
            reply_markup=get_main_keyboard()
        )

    else:
        logger.warning(f"Неизвестный callback: {data}")
        await query.answer("Команда не распознана")


async def send_vacancy_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               index: int, query=None):
    """Вспомогательная функция для отправки вакансии с кнопками"""
    vacancies = context.user_data.get('search_results', [])

    if index < 0 or index >= len(vacancies):
        logger.error(f"Индекс {index} вне диапазона (0-{len(vacancies) - 1})")
        return

    vacancy_data = vacancies[index]
    vacancy_id = vacancy_data.get('id', '')

    try:
        # Сохраняем в БД
        async for session in db.get_session():
            await vacancy_repo.save_vacancy(session, vacancy_data)
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

        # Обновляем сообщение
        if query:
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            # Это fallback, если query не передан
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
        error_msg = "⚠️ Ошибка при обработке вакансии"
        if query:
            await query.edit_message_text(error_msg, reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text(error_msg, reply_markup=get_main_keyboard())


def setup_callback_handlers(application):
    """Регистрация обработчиков callback-кнопок"""
    # Регистрируем общий обработчик для всех callback
    application.add_handler(CallbackQueryHandler(handle_callback_query))