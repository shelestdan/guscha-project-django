"""Улучшенная команда управления Telegram ботом с graceful shutdown."""

import asyncio
import signal
import sys
import logging
from typing import Optional
from django.core.management.base import BaseCommand, CommandError
from telegram_bot.bot import get_bot_instance, TelegramBot
from telegram_bot.exceptions import ConfigurationError, TelegramBotError
from telegram_bot.config.settings import bot_settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Команда для запуска Telegram бота с современным управлением жизненным циклом."""
    
    help = 'Запуск Telegram бота с graceful shutdown и мониторингом'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot: Optional[TelegramBot] = None
        self.should_stop = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.shutdown_timeout = 30  # секунд на graceful shutdown
    
    def add_arguments(self, parser):
        """Добавляет аргументы командной строки."""
        parser.add_argument(
            '--async',
            action='store_true',
            help='Запустить бота в асинхронном режиме'
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Выполнить проверку здоровья бота и выйти'
        )
        parser.add_argument(
            '--info',
            action='store_true',
            help='Показать информацию о боте и выйти'
        )
        parser.add_argument(
            '--shutdown-timeout',
            type=int,
            default=30,
            help='Таймаут для graceful shutdown в секундах (по умолчанию: 30)'
        )
    
    def handle(self, *args, **options):
        """Основной метод команды."""
        try:
            # Настраиваем таймаут shutdown
            self.shutdown_timeout = options['shutdown_timeout']
            
            # Обрабатываем специальные команды
            if options['health_check']:
                self._perform_health_check()
                return
            
            if options['info']:
                self._show_bot_info()
                return
            
            # Получаем экземпляр бота
            self.bot = get_bot_instance()
            
            # Настраиваем обработчики сигналов
            self._setup_signal_handlers()
            
            self.stdout.write(
                self.style.SUCCESS('🚀 Запуск Telegram бота...')
            )
            
            # Запускаем бота в зависимости от режима
            if options['async']:
                self._run_async_bot()
            else:
                self._run_sync_bot()
                
        except ConfigurationError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка конфигурации: {e}')
            )
            raise CommandError(f'Ошибка конфигурации: {e}')
        except TelegramBotError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка Telegram бота: {e}')
            )
            raise CommandError(f'Ошибка бота: {e}')
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('⚠️ Получен сигнал прерывания')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Неожиданная ошибка: {e}')
            )
            logger.error(f'Неожиданная ошибка при запуске бота: {e}', exc_info=True)
            raise CommandError(f'Неожиданная ошибка: {e}')
        finally:
            self.stdout.write(
                self.style.SUCCESS('✅ Telegram бот остановлен')
            )
    
    def _setup_signal_handlers(self):
        """Настраивает обработчики сигналов для graceful shutdown."""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.stdout.write(
                self.style.WARNING(f'⚠️ Получен сигнал {signal_name}, начинаем graceful shutdown...')
            )
            self.should_stop = True
            
            # Для асинхронного режима создаем задачу остановки
            if self.loop and not self.loop.is_closed():
                self.loop.create_task(self._stop_bot_gracefully())
        
        # Настраиваем обработчики для разных платформ
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGHUP, signal_handler)
        else:
            # Windows поддерживает только SIGINT
            signal.signal(signal.SIGINT, signal_handler)
    
    def _run_sync_bot(self):
        """Запускает бота в синхронном режиме."""
        try:
            self.stdout.write(
                self.style.SUCCESS('🔄 Запуск в синхронном режиме...')
            )
            self.bot.start_bot()
        except Exception as e:
            logger.error(f'Ошибка в синхронном режиме: {e}')
            raise
    
    def _run_async_bot(self):
        """Запускает бота в асинхронном режиме."""
        try:
            self.stdout.write(
                self.style.SUCCESS('🔄 Запуск в асинхронном режиме...')
            )
            
            # Создаем и настраиваем event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Настраиваем обработчики сигналов для asyncio
            if sys.platform != 'win32':
                for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                    self.loop.add_signal_handler(
                        sig, 
                        lambda s=sig: self.loop.create_task(
                            self._handle_signal_async(s)
                        )
                    )
            
            # Запускаем бота
            self.loop.run_until_complete(self.bot.start_bot_async())
            
        except Exception as e:
            logger.error(f'Ошибка в асинхронном режиме: {e}')
            raise
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()
    
    async def _handle_signal_async(self, signum):
        """Обрабатывает сигналы в асинхронном режиме."""
        signal_name = signal.Signals(signum).name
        self.stdout.write(
            self.style.WARNING(f'⚠️ Получен сигнал {signal_name}, начинаем graceful shutdown...')
        )
        self.should_stop = True
        await self._stop_bot_gracefully()
    
    async def _stop_bot_gracefully(self):
        """Корректно останавливает бота с таймаутом."""
        if not self.bot:
            return
        
        try:
            self.stdout.write(
                self.style.WARNING(f'🛑 Начинаем graceful shutdown (таймаут: {self.shutdown_timeout}с)...')
            )
            
            # Останавливаем бота с таймаутом
            shutdown_task = asyncio.create_task(self.bot.stop_bot())
            
            try:
                await asyncio.wait_for(shutdown_task, timeout=self.shutdown_timeout)
                self.stdout.write(
                    self.style.SUCCESS('✅ Graceful shutdown завершен успешно')
                )
            except asyncio.TimeoutError:
                self.stdout.write(
                    self.style.ERROR(f'❌ Таймаут graceful shutdown ({self.shutdown_timeout}с), принудительная остановка')
                )
                shutdown_task.cancel()
                
                # Даем время на отмену задачи
                try:
                    await shutdown_task
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            logger.error(f'Ошибка при graceful shutdown: {e}')
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при остановке бота: {e}')
            )
    
    def _perform_health_check(self):
        """Выполняет проверку здоровья бота."""
        try:
            self.stdout.write(
                self.style.SUCCESS('🏥 Выполняем проверку здоровья бота...')
            )
            
            # Проверяем конфигурацию
            try:
                bot = get_bot_instance()
                self.stdout.write(
                    self.style.SUCCESS('✅ Конфигурация бота: OK')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Конфигурация бота: FAIL - {e}')
                )
                return
            
            # Проверяем настройки
            self.stdout.write(
                self.style.SUCCESS(f'✅ Настройки загружены: {bot_settings.token[:10]}...')
            )
            
            # Проверяем инициализацию сервисов
            bot_info = bot.get_bot_info()
            if bot_info['services_initialized']:
                self.stdout.write(
                    self.style.SUCCESS('✅ Сервисы инициализированы: OK')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Сервисы инициализированы: FAIL')
                )
            
            self.stdout.write(
                self.style.SUCCESS('🎉 Проверка здоровья завершена успешно')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при проверке здоровья: {e}')
            )
            logger.error(f'Ошибка health check: {e}', exc_info=True)
    
    def _show_bot_info(self):
        """Показывает информацию о боте."""
        try:
            self.stdout.write(
                self.style.SUCCESS('ℹ️ Информация о Telegram боте:')
            )
            
            bot = get_bot_instance()
            bot_info = bot.get_bot_info()
            
            # Основная информация
            self.stdout.write(f"📊 Статус: {'Запущен' if bot_info['is_running'] else 'Остановлен'}")
            self.stdout.write(f"🤖 Username: {bot_info['bot_username'] or 'Не определен'}")
            self.stdout.write(f"🔧 Обработчиков: {bot_info['handlers_count']}")
            self.stdout.write(f"⚙️ Сервисы: {'Инициализированы' if bot_info['services_initialized'] else 'Не инициализированы'}")
            
            # Настройки
            self.stdout.write("\n📋 Настройки:")
            self.stdout.write(f"  • Таймаут верификации: {bot_settings.verification_code_timeout_minutes} мин")
            self.stdout.write(f"  • Лимит регистрации: {bot_settings.max_registration_attempts} попыток за {bot_settings.registration_rate_limit_minutes} мин")
            self.stdout.write(f"  • Уровень логирования: {bot_settings.log_level}")
            
            # Архитектура
            self.stdout.write("\n🏗️ Архитектура:")
            self.stdout.write("  • Слоистая архитектура с DI")
            self.stdout.write("  • Handlers -> Services -> Repositories")
            self.stdout.write("  • Централизованная обработка ошибок")
            self.stdout.write("  • Rate limiting")
            self.stdout.write("  • Валидация данных")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при получении информации о боте: {e}')
            )
            logger.error(f'Ошибка получения информации о боте: {e}', exc_info=True)
    
    def _log_startup_info(self):
        """Логирует информацию о запуске."""
        logger.info("=" * 50)
        logger.info("🚀 ЗАПУСК TELEGRAM БОТА")
        logger.info("=" * 50)
        logger.info(f"📊 Версия Python: {sys.version}")
        logger.info(f"🔧 Уровень логирования: {bot_settings.log_level}")
        logger.info(f"⚙️ Таймаут верификации: {bot_settings.verification_code_timeout_minutes} мин")
        logger.info(f"🛡️ Лимит регистрации: {bot_settings.max_registration_attempts} попыток")
        logger.info("=" * 50)