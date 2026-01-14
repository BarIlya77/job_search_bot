from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from src.core.logger import get_logger
from src.storage.database import db
from src.storage.repositories.filter_repo import filter_repo
from src.utils.filter_keyboards import (
    get_filters_main_keyboard, get_profession_keyboard, get_salary_keyboard,
    get_experience_keyboard, get_schedule_keyboard, get_employment_keyboard,
    get_area_keyboard, get_confirmation_keyboard
)
from src.utils.keyboards import get_main_keyboard

logger = get_logger(__name__)


class FilterHandler:
    """Обработчик фильтров поиска"""

    def __init__(self):
        self.waiting_for_input = {}  # {user_id: filter_type}

    async def show_filters_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню фильтров"""
        query = update.callback_query
        user_id = query.from_user.id

        # Получаем текущие фильтры пользователя
        current_filters = {}
        async for session in db.get_session():
            current_filters = await filter_repo.get_all_filters(session, user_id)

        # Показываем меню
        await query.edit_message_text(
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

    async def handle_filter_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора типа фильтра"""
        query = update.callback_query
        data = query.data

        if data == "filter_profession":
            await query.edit_message_text(
                "💼 *Выберите профессию:*\n\n"
                "Или введите свою профессию вручную",
                parse_mode='Markdown',
                reply_markup=get_profession_keyboard()
            )

        elif data == "filter_salary":
            await query.edit_message_text(
                "💰 *Выберите минимальную зарплату:*\n\n"
                "Или введите свою сумму в рублях",
                parse_mode='Markdown',
                reply_markup=get_salary_keyboard()
            )

        elif data == "filter_experience":
            await query.edit_message_text(
                "🎓 *Выберите требуемый опыт:*",
                parse_mode='Markdown',
                reply_markup=get_experience_keyboard()
            )

        elif data == "filter_schedule":
            await query.edit_message_text(
                "📍 *Выберите формат работы:*",
                parse_mode='Markdown',
                reply_markup=get_schedule_keyboard()
            )

        elif data == "filter_employment":
            await query.edit_message_text(
                "🏢 *Выберите тип занятости:*",
                parse_mode='Markdown',
                reply_markup=get_employment_keyboard()
            )

        elif data == "filter_area":
            await query.edit_message_text(
                "🌍 *Выберите город:*\n\n"
                "Или введите свой город",
                parse_mode='Markdown',
                reply_markup=get_area_keyboard()
            )

        elif data == "filter_keywords":
            self.waiting_for_input[query.from_user.id] = "keywords"
            await query.edit_message_text(
                "🔍 *Введите ключевые слова:*\n\n"
                "Например: Django, FastAPI, PostgreSQL, Docker\n"
                "Каждое слово или фраза с новой строки",
                parse_mode='Markdown',
                reply_markup=get_confirmation_keyboard("back")
            )

    async def handle_filter_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора значения фильтра"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id

        if data.startswith("prof_"):
            profession = data.replace("prof_", "")
            if profession == "custom_profession":
                self.waiting_for_input[user_id] = "profession"
                await query.edit_message_text(
                    "💼 *Введите профессию:*\n\n"
                    "Например: Python-разработчик, Data Scientist",
                    parse_mode='Markdown'
                )
            else:
                async for session in db.get_session():
                    await filter_repo.save_filter(session, user_id, "profession", profession)
                await self.show_filters_menu(update, context)

        elif data.startswith("salary_"):
            salary = data.replace("salary_", "")
            if salary == "custom_salary":
                self.waiting_for_input[user_id] = "salary"
                await query.edit_message_text(
                    "💰 *Введите минимальную зарплату:*\n\n"
                    "Только цифры, например: 120000",
                    parse_mode='Markdown'
                )
            else:
                # Парсим диапазон зарплат
                if "_" in salary:
                    salary_min = salary.split("_")[0]
                elif salary == "any":
                    salary_min = None
                else:
                    salary_min = salary

                async for session in db.get_session():
                    if salary_min:
                        await filter_repo.save_filter(session, user_id, "salary_min", int(salary_min))
                    else:
                        await filter_repo.delete_filter(session, user_id, "salary_min")
                await self.show_filters_menu(update, context)

        elif data.startswith("exp_"):
            experience = data.replace("exp_", "")
            async for session in db.get_session():
                await filter_repo.save_filter(session, user_id, "experience", experience)
            await self.show_filters_menu(update, context)

        elif data.startswith("schedule_"):
            schedule = data.replace("schedule_", "")
            async for session in db.get_session():
                await filter_repo.save_filter(session, user_id, "schedule", schedule)
            await self.show_filters_menu(update, context)

        elif data.startswith("employment_"):
            employment = data.replace("employment_", "")
            async for session in db.get_session():
                await filter_repo.save_filter(session, user_id, "employment", employment)
            await self.show_filters_menu(update, context)

        elif data.startswith("area_"):
            area = data.replace("area_", "")
            if area == "custom_area":
                self.waiting_for_input[user_id] = "area"
                await query.edit_message_text(
                    "🌍 *Введите город:*\n\n"
                    "Например: Москва, Санкт-Петербург, Новосибирск",
                    parse_mode='Markdown'
                )
            else:
                async for session in db.get_session():
                    await filter_repo.save_filter(session, user_id, "area", area)
                await self.show_filters_menu(update, context)

    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстового ввода для фильтров"""
        user_id = update.effective_user.id
        text = update.message.text

        if user_id not in self.waiting_for_input:
            return

        filter_type = self.waiting_for_input.pop(user_id)

        async for session in db.get_session():
            if filter_type == "profession":
                await filter_repo.save_filter(session, user_id, "profession", text)
                await update.message.reply_text(
                    f"✅ Профессия сохранена: *{text}*",
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard()
                )

            elif filter_type == "salary":
                try:
                    salary = int(''.join(filter(str.isdigit, text)))
                    await filter_repo.save_filter(session, user_id, "salary_min", salary)
                    await update.message.reply_text(
                        f"✅ Минимальная зарплата: *{salary:,} руб.*".replace(',', ' '),
                        parse_mode='Markdown',
                        reply_markup=get_main_keyboard()
                    )
                except ValueError:
                    await update.message.reply_text(
                        "❌ Пожалуйста, введите только цифры",
                        reply_markup=get_main_keyboard()
                    )

            elif filter_type == "area":
                await filter_repo.save_filter(session, user_id, "area", text)
                await update.message.reply_text(
                    f"✅ Город сохранен: *{text}*",
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard()
                )

            elif filter_type == "keywords":
                keywords = [k.strip() for k in text.split('\n') if k.strip()]
                await filter_repo.save_filter(session, user_id, "keywords", keywords)
                await update.message.reply_text(
                    f"✅ Ключевые слова сохранены:\n" + "\n".join(f"• {k}" for k in keywords),
                    reply_markup=get_main_keyboard()
                )

        # Показываем меню фильтров
        await self.show_filters_menu(update, context)

    async def handle_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка действий с фильтрами"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id

        if data == "filters_save":
            # Формируем текстовый запрос для API HH
            async for session in db.get_session():
                filters = await filter_repo.get_all_filters(session, user_id)

            search_text = self._build_search_query(filters)

            # Сохраняем в старую систему (для совместимости)
            async for session in db.get_session():
                from src.storage.repositories.user_repo import user_repo
                await user_repo.update_filters(session, user_id, search_text)

            await query.edit_message_text(
                f"✅ *Фильтры сохранены!*\n\n"
                f"Поисковый запрос:\n`{search_text}`\n\n"
                f"Теперь используйте 🔍 Поиск вакансий",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )

        elif data == "filters_clear":
            async for session in db.get_session():
                await filter_repo.clear_all_filters(session, user_id)

            await query.edit_message_text(
                "🧹 *Все фильтры очищены!*",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )

        elif data == "filters_back" or data == "back_to_filters":
            await self.show_filters_menu(update, context)

        elif data == "back_to_main":
            await query.edit_message_text(
                "Главное меню:",
                reply_markup=get_main_keyboard()
            )

        elif data.startswith("confirm_back"):
            user_id = query.from_user.id
            if user_id in self.waiting_for_input:
                del self.waiting_for_input[user_id]
            await self.show_filters_menu(update, context)

        elif data.startswith("cancel_back"):
            user_id = query.from_user.id
            # Просто удаляем клавиатуру, оставляя текст
            await query.edit_message_text(
                query.message.text,
                parse_mode='Markdown'
            )

    def _build_search_query(self, filters: dict) -> str:
        """Собирает текстовый запрос из структурированных фильтров"""
        parts = []

        if filters.get('profession'):
            parts.append(filters['profession'])

        if filters.get('experience'):
            exp_map = {
                'noExperience': 'без опыта',
                'junior': 'junior',
                'middle': 'middle',
                'senior': 'senior',
                'lead': 'lead'
            }
            parts.append(exp_map.get(filters['experience'], filters['experience']))

        if filters.get('area') and filters['area'] not in ['any', 'remote']:
            parts.append(filters['area'])

        if filters.get('keywords'):
            parts.extend(filters['keywords'])

        return ' '.join(parts)


# Создаем экземпляр обработчика
filter_handler = FilterHandler()


def setup_filter_handlers(application):
    """Регистрация обработчиков фильтров"""
    # Обработчики callback-кнопок - более специфичные паттерны
    application.add_handler(CallbackQueryHandler(
        filter_handler.show_filters_menu, pattern="^filters_menu$"
    ))
    application.add_handler(CallbackQueryHandler(
        filter_handler.handle_filter_selection, pattern="^filter_(?!next|prev|save|hide|cover|gen_cover|back_to|ignore)"
    ))
    application.add_handler(CallbackQueryHandler(
        filter_handler.handle_filter_value, pattern="^(prof|salary|exp|schedule|employment|area)_"
    ))
    application.add_handler(CallbackQueryHandler(
        filter_handler.handle_actions, pattern="^filters_(save|clear|back)|^back_to_filters$|^confirm_|^cancel_"
    ))

    # Обработчик текстового ввода
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, filter_handler.handle_text_input
    ))