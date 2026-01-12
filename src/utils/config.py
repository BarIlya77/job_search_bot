import os
from dotenv import load_dotenv
from pathlib import Path


# class Config:
#     """Класс для хранения конфигурации"""
#
#     def __init__(self):
#         # Загружаем переменные окружения из файла .env
#         env_path = Path(__file__).parent.parent.parent / 'configs' / 'dev.env'
#         load_dotenv(env_path)
#
#         self.telegram_token = os.getenv('TELEGRAM_TOKEN')
#         self.hh_api_url = os.getenv('HH_API_URL', 'https://api.hh.ru/vacancies')
#         self.check_interval = int(os.getenv('CHECK_INTERVAL', '3600'))  # 1 час по умолчанию

class Config:
    def __init__(self):
        env_path = Path(__file__).parent.parent.parent / 'configs' / 'dev.env'
        load_dotenv(env_path)

        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.hh_api_url = os.getenv('HH_API_URL', 'https://api.hh.ru/vacancies')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '3600'))  # 1 час по умолчанию

        # Настройки PostgreSQL
        self.db_config = {
            "host": os.getenv('DB_HOST', 'localhost'),
            "port": os.getenv('DB_PORT', 5432),
            "database": os.getenv('DB_NAME', 'job_bot'),
            "user": os.getenv('DB_USER', 'bot_user'),
            "password": os.getenv('DB_PASSWORD', 'bot_password')
        }

    def get_db_dsn(self):
        """Формирует строку подключения к БД"""
        return f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"


def load_config():
    """Загружает и возвращает конфигурацию"""
    return Config()
