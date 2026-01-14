import asyncio
from src.core.logger import get_logger
from src.storage.database import db
from src.storage.repositories.user_repo import user_repo
from src.storage.repositories.vacancy_repo import vacancy_repo
from src.services.filter_service import filter_service
from src.services.hh_client import hh_client
from src.handlers.notifications import send_vacancy_notification

logger = get_logger(__name__)


class JobScheduler:
    def __init__(self, application, check_interval):
        self.application = application
        self.is_running = False
        self.check_interval = check_interval
        self.task = None

    async def start(self):
        self.is_running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"Планировщик запущен. Интервал проверки: {self.check_interval} сек.")

    async def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Планировщик остановлен")

    async def _scheduler_loop(self):
        # Первая проверка через 30 секунд после старта
        await asyncio.sleep(30)

        while self.is_running:
            try:
                await self.check_new_vacancies()
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(self.check_interval)

    async def check_new_vacancies(self):
        """Проверка новых вакансий для всех активных пользователей"""
        logger.info("🔄 Запуск периодической проверки новых вакансий")

        # Получаем всех активных пользователей
        async for session in db.get_session():
            users = await user_repo.get_active_users(session)

            if not users:
                logger.info("Нет активных пользователей для проверки")
                return

            logger.info(f"Проверяем вакансии для {len(users)} активных пользователей")

            for user in users:
                try:
                    await self.check_vacancies_for_user(user.telegram_id)
                    # Пауза между запросами для разных пользователей
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Ошибка при проверке вакансий для пользователя {user.telegram_id}: {e}")

    async def check_vacancies_for_user(self, telegram_id: int):
        """Проверка новых вакансий для конкретного пользователя"""
        logger.debug(f"Проверка вакансий для пользователя {telegram_id}")

        # 1. Получаем фильтры пользователя
        filters = await filter_service.get_user_filters(telegram_id)
        if not filters:
            logger.debug(f"У пользователя {telegram_id} нет фильтров, пропускаем")
            return

        # 2. Преобразуем фильтры в параметры HH API
        params = await filter_service.to_hh_params(filters)
        # Добавим базовые параметры
        params.update({
            'per_page': 20,  # Первые 20 самых свежих вакансий
            'order_by': 'publication_time',
            'search_field': 'name'
        })

        # 3. Ищем вакансии
        try:
            vacancies = await hh_client.search_vacancies(**params)
        except Exception as e:
            logger.error(f"Ошибка при поиске вакансий для пользователя {telegram_id}: {e}")
            return

        if not vacancies:
            logger.debug(f"Для пользователя {telegram_id} не найдено новых вакансий")
            return

        logger.info(f"Для пользователя {telegram_id} найдено {len(vacancies)} вакансий")

        # 4. Обрабатываем каждую вакансию
        new_vacancies_count = 0
        for vacancy_data in vacancies:
            if await self.process_vacancy_for_user(telegram_id, vacancy_data):
                new_vacancies_count += 1

        if new_vacancies_count:
            logger.info(f"Отправлено {new_vacancies_count} новых вакансий пользователю {telegram_id}")

    async def process_vacancy_for_user(self, telegram_id: int, vacancy_data: dict) -> bool:
        """Обработка вакансии для пользователя: сохранение и отправка уведомления, если новая"""
        vacancy_id = str(vacancy_data.get('id', ''))

        if not vacancy_id:
            return False

        async for session in db.get_session():
            try:
                # Проверяем, отправляли ли уже эту вакансию пользователю
                user_vacancy = await vacancy_repo.get_user_vacancy(session, telegram_id, vacancy_id)
                if user_vacancy and user_vacancy.notified:
                    # Уже отправляли
                    return False

                # Сохраняем вакансию в БД
                vacancy = await vacancy_repo.save_vacancy(session, vacancy_data)

                # Отправляем уведомление
                await send_vacancy_notification(self.application.bot, telegram_id, vacancy_data)

                # Отмечаем как отправленную
                await vacancy_repo.mark_as_notified(session, telegram_id, vacancy_id)
                logger.info(f"📨 Отправлена новая вакансия {vacancy_id} пользователю {telegram_id}")
                return True

            except Exception as e:
                logger.error(f"Ошибка обработки вакансии {vacancy_id} для {telegram_id}: {e}")
                return False
