import asyncio
import signal
import sys
from django.core.management.base import BaseCommand
from telegram_bot.bot import get_bot_instance
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запуск Telegram бота'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = None
        self.should_stop = False
        self.loop = None
    
    def handle(self, *args, **options):
        """Основной метод команды"""
        try:
            # Получаем экземпляр бота
            self.bot = get_bot_instance()
            
            self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))
            
            # Запуск бота (теперь синхронный)
            self.bot.start_bot()
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Получен сигнал прерывания'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при запуске бота: {e}'))
            logger.error(f'Ошибка при запуске бота: {e}')
        finally:
            self.stdout.write(self.style.SUCCESS('Telegram бот остановлен'))
    
    def signal_handler(self):
        """Обработчик сигналов остановки"""
        self.stdout.write(self.style.WARNING('Получен сигнал остановки'))
        self.should_stop = True
        if self.loop and not self.loop.is_closed():
            self.loop.create_task(self.stop_bot_gracefully())
    
    async def stop_bot_gracefully(self):
        """Корректная остановка бота"""
        if self.bot:
            await self.bot.stop_bot()
    
    async def run_bot(self):
        """Запуск бота в асинхронном режиме"""
        self.loop = asyncio.get_event_loop()
        
        # Настройка обработчиков сигналов для asyncio
        if sys.platform != 'win32':
            for sig in (signal.SIGTERM, signal.SIGINT):
                self.loop.add_signal_handler(sig, self.signal_handler)
        
        try:
            # Запуск бота (теперь асинхронный)
            await self.bot.start_bot()
        except asyncio.CancelledError:
            logger.info('Бот был отменен')
        except Exception as e:
            logger.error(f'Ошибка в работе бота: {e}')
            raise
        finally:
            # Остановка бота
            if self.bot:
                try:
                    await self.bot.stop_bot()
                except Exception as e:
                    logger.error(f'Ошибка при остановке бота: {e}')