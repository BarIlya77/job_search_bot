import asyncio
# import logging
import nest_asyncio
from telegram.ext import Application
from src.core.logger import get_logger
from src.utils.config import load_config
from src.handlers.commands import setup_handlers
from src.storage.database import db
from src.handlers.messages import setup_message_handlers
from src.handlers.callbacks import setup_callback_handlers
from src.handlers.filters import setup_filter_handlers


# Разрешаем вложенные event loops
nest_asyncio.apply()

# Настройка логирования
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)
logger = get_logger(__name__)

async def main():
    """Основная функция запуска бота"""
    # Загружаем конфигурацию
    config = load_config()

    if not config.telegram_token:
        logger.error("Токен Telegram не найден! Проверьте configs/dev.env")
        return

    # 1. ПОДКЛЮЧАЕМСЯ К БД (создаем engine)
    await db.connect()

    # 2. СОЗДАЕМ ТАБЛИЦЫ (если их нет)
    await db.create_tables()

    logger.info("✅ База данных подключена")

    # 3. ЗАПУСКАЕМ БОТА
    application = Application.builder().token(config.telegram_token).build()
    setup_handlers(application)  # Команды
    setup_message_handlers(application)  # Текстовые сообщения (кнопки)
    setup_callback_handlers(application)  # Inline-кнопки
    setup_filter_handlers(application)

    logger.info("🚀 Бот запущен с SQLAlchemy!")

    # Используем синхронный запуск polling внутри асинхронной функции
    await application.run_polling()




def start_bot():
    """Точка входа"""
    # Создаем новый event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    finally:
        loop.close()


if __name__ == '__main__':
    start_bot()