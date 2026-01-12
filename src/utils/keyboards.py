from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode


# REPLY KEYBOARD (постоянная)
def get_main_keyboard():
    """Основная клавиатура команд"""
    keyboard = [
        ["🔍 Поиск вакансий", "⚙️ Мои фильтры"],
        ["📊 Мой статус", "🆘 Помощь"],
        ["⏸️ Остановить", "▶️ Возобновить"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_filters_keyboard():
    """Клавиатура для работы с фильтрами"""
    keyboard = [
        ["📝 Установить фильтры", "👀 Показать фильтры"],
        ["🧹 Очистить фильтры", "🔙 Назад в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_search_keyboard():
    """Клавиатура для поиска"""
    keyboard = [
        ["🔎 Искать сейчас", "⏰ Автопоиск"],
        ["📋 История поиска", "🔙 Назад в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# INLINE KEYBOARD (для вакансий)
def get_vacancy_keyboard(vacancy_id: str, page: int = 0, total: int = 1):
    """Inline-клавиатура для действий с вакансией"""
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"prev_{page - 1}"))

    nav_buttons.append(InlineKeyboardButton(f"{page + 1}/{total}", callback_data="page_info"))

    if page < total - 1:
        nav_buttons.append(InlineKeyboardButton("Следующая ➡️", callback_data=f"next_{page + 1}"))

    keyboard = [
        [
            InlineKeyboardButton("📨 Создать письмо", callback_data=f"cover_{vacancy_id}"),
            InlineKeyboardButton("💾 Сохранить", callback_data=f"save_{vacancy_id}")
        ],
        [
            InlineKeyboardButton("👎 Не интересно", callback_data=f"hide_{vacancy_id}"),
            InlineKeyboardButton("❌ Скрыть", callback_data=f"ignore_{vacancy_id}")
        ],
        nav_buttons,
        [
            InlineKeyboardButton("🔗 Открыть на HH", url=f"https://hh.ru/vacancy/{vacancy_id}")
        ]
    ]

    # Убираем пустые строки
    keyboard = [row for row in keyboard if row]
    return InlineKeyboardMarkup(keyboard)


def get_cover_letter_keyboard(vacancy_id: str):
    """Клавиатура для сопроводительного письма"""
    keyboard = [
        [
            InlineKeyboardButton("🤖 Сгенерировать", callback_data=f"gen_cover_{vacancy_id}"),
            InlineKeyboardButton("✏️ Ввести вручную", callback_data=f"manual_cover_{vacancy_id}")
        ],
        [
            InlineKeyboardButton("📤 Отправить", callback_data=f"send_cover_{vacancy_id}"),
            InlineKeyboardButton("💾 Черновик", callback_data=f"draft_cover_{vacancy_id}")
        ],
        [
            InlineKeyboardButton("↩️ Назад к вакансии", callback_data=f"back_to_{vacancy_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action: str, data: str):
    """Клавиатура подтверждения действия"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{action}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)