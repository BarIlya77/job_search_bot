import asyncio
import nest_asyncio
from telegram.ext import Application
from src.core.logger import get_logger
from src.utils.config import load_config
from src.handlers.commands import setup_handlers
from src.storage.database import db
from src.handlers.messages import setup_message_handlers
from src.handlers.callbacks import setup_callback_handlers
from src.handlers.filters import setup_filter_handlers
from src.core.scheduler import JobScheduler  # Импортируем планировщик

nest_asyncio.apply()
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

    # Порядок регистрации обработчиков:
    setup_handlers(application)  # Команды
    setup_message_handlers(application)  # Текстовые сообщения
    setup_callback_handlers(application)  # Callback-кнопки - ДО фильтров
    setup_filter_handlers(application)  # Фильтры - ПОСЛЕ общих колбэков

    # 4. ЗАПУСКАЕМ ПЛАНИРОВЩИК
    scheduler = JobScheduler(application, config.check_interval)
    await scheduler.start()

    logger.info("🚀 Бот запущен с SQLAlchemy и планировщиком!")

    try:
        await application.run_polling()
    except KeyboardInterrupt:
        logger.info("Бот остановлен по команде пользователя")
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")
    finally:
        await scheduler.stop()


def start_bot():
    """Точка входа"""
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