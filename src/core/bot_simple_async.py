#!/usr/bin/env python3
"""
ПРОСТОЙ АСИНХРОННЫЙ БОТ БЕЗ ПРОБЛЕМ С ЗАВЕРШЕНИЕМ
"""
import asyncio
import logging
from telegram.ext import Application
from src.utils.config import load_config
from src.handlers.commands import setup_handlers
from src.storage.database import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    # Загрузка конфигурации
    config = load_config()
    if not config.telegram_token:
        logger.error("❌ Токен не найден")
        return

    # Подключение БД
    await db.connect()
    await db.create_tables()
    logger.info("✅ БД подключена")

    # Создание и запуск бота
    app = Application.builder().token(config.telegram_token).build()
    setup_handlers(app)

    logger.info("🚀 Бот запущен! Нажмите Ctrl+C для остановки.")

    # Запуск с обработкой Ctrl+C
    await app.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✅ Бот корректно остановлен")