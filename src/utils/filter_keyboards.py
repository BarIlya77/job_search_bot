from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional


def get_filters_main_keyboard(current_filters: dict = None) -> InlineKeyboardMarkup:
    """Главное меню фильтров с отображением текущих настроек"""
    filters_text = ""
    if current_filters:
        if current_filters.get('profession'):
            filters_text += f"💼 {current_filters['profession']}\n"
        if current_filters.get('salary_min'):
            filters_text += f"💰 от {current_filters['salary_min']} руб.\n"
        if current_filters.get('experience'):
            filters_text += f"🎓 {current_filters['experience']}\n"

    keyboard = [
        [InlineKeyboardButton("💼 Профессия", callback_data="filter_profession")],
        [InlineKeyboardButton("💰 Зарплата", callback_data="filter_salary")],
        [InlineKeyboardButton("🎓 Опыт", callback_data="filter_experience")],
        [InlineKeyboardButton("📍 Формат работы", callback_data="filter_schedule")],
        [InlineKeyboardButton("🏢 Тип занятости", callback_data="filter_employment")],
        [InlineKeyboardButton("🌍 Город", callback_data="filter_area")],
        [InlineKeyboardButton("🔍 Ключевые слова", callback_data="filter_keywords")],
        [
            InlineKeyboardButton("✅ Сохранить", callback_data="filters_save"),
            InlineKeyboardButton("🧹 Очистить все", callback_data="filters_clear")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="filters_back")]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_profession_keyboard() -> InlineKeyboardMarkup:
    """Выбор профессии"""
    professions = [
        ("Python-разработчик", "Python"),
        ("Data Scientist", "Data Science"),
        ("Backend-разработчик", "Backend"),
        ("Frontend-разработчик", "Frontend"),
        ("DevOps", "DevOps"),
        ("Аналитик данных", "Analyst"),
        ("Тестировщик QA", "QA"),
        ("Менеджер проектов", "PM"),
        ("Другая...", "custom_profession")
    ]

    keyboard = []
    for i in range(0, len(professions), 2):
        row = []
        if i < len(professions):
            row.append(InlineKeyboardButton(professions[i][0],
                                            callback_data=f"prof_{professions[i][1]}"))
        if i + 1 < len(professions):
            row.append(InlineKeyboardButton(professions[i + 1][0],
                                            callback_data=f"prof_{professions[i + 1][1]}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_filters")])
    return InlineKeyboardMarkup(keyboard)


def get_salary_keyboard() -> InlineKeyboardMarkup:
    """Выбор зарплаты"""
    salary_ranges = [
        ("💸 Любая", "any"),
        ("💰 До 50 000", "50000"),
        ("💰 50 000 - 100 000", "50000_100000"),
        ("💰 100 000 - 200 000", "100000_200000"),
        ("💰 200 000+", "200000"),
        ("💰 Указать свою", "custom_salary")
    ]

    keyboard = [[InlineKeyboardButton(text, callback_data=f"salary_{value}")]
                for text, value in salary_ranges]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_filters")])

    return InlineKeyboardMarkup(keyboard)


def get_experience_keyboard() -> InlineKeyboardMarkup:
    """Выбор опыта"""
    experiences = [
        ("👶 Без опыта", "noExperience"),
        ("👨‍🎓 Junior", "junior"),
        ("👨‍💼 Middle", "middle"),
        ("👴 Senior", "senior"),
        ("👑 Lead", "lead")
    ]

    keyboard = [[InlineKeyboardButton(text, callback_data=f"exp_{value}")]
                for text, value in experiences]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_filters")])

    return InlineKeyboardMarkup(keyboard)


def get_schedule_keyboard() -> InlineKeyboardMarkup:
    """Выбор формата работы"""
    schedules = [
        ("🏢 Офис", "office"),
        ("🏠 Удалённо", "remote"),
        ("🔀 Гибрид", "hybrid"),
        ("🌍 Любой", "any")
    ]

    keyboard = [[InlineKeyboardButton(text, callback_data=f"schedule_{value}")]
                for text, value in schedules]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_filters")])

    return InlineKeyboardMarkup(keyboard)


def get_employment_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа занятости"""
    employments = [
        ("📅 Полный день", "fullDay"),
        ("⏰ Частичная", "partDay"),
        ("📝 Проектная", "project"),
        ("🎓 Стажировка", "internship"),
        ("🔄 Сменная", "shift")
    ]

    keyboard = [[InlineKeyboardButton(text, callback_data=f"employment_{value}")]
                for text, value in employments]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_filters")])

    return InlineKeyboardMarkup(keyboard)


def get_area_keyboard() -> InlineKeyboardMarkup:
    """Выбор города"""
    areas = [
        ("📍 Москва", "1"),
        ("📍 Санкт-Петербург", "2"),
        ("📍 Удалённо", "remote"),
        ("📍 Любой город", "any"),
        ("📍 Выбрать другой...", "custom_area")
    ]

    keyboard = []
    for i in range(0, len(areas), 2):
        row = []
        if i < len(areas):
            row.append(InlineKeyboardButton(areas[i][0],
                                            callback_data=f"area_{areas[i][1]}"))
        if i + 1 < len(areas):
            row.append(InlineKeyboardButton(areas[i + 1][0],
                                            callback_data=f"area_{areas[i + 1][1]}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_filters")])
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action: str, data: str = "") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{action}")
        ]
    ])
