"""Репозиторий для работы с QR-кодами."""

from typing import Optional, List
from asgiref.sync import sync_to_async
from django.utils import timezone

from apps.accounts.models import QRCodeScan, TelegramVerificationCode
from ..exceptions import DatabaseError


class QRCodeRepository:
    """Репозиторий для работы с QR-кодами."""
    
    @staticmethod
    async def get_by_qr_id(qr_id: str) -> Optional[QRCodeScan]:
        """Получает QR-код по ID."""
        try:
            return await sync_to_async(
                QRCodeScan.objects.filter(
                    qr_id=qr_id
                ).select_related('verification_code').first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения QR-кода по ID: {e}")
    
    @staticmethod
    async def get_by_verification_code(
        verification_code: TelegramVerificationCode
    ) -> Optional[QRCodeScan]:
        """Получает QR-код по коду верификации."""
        try:
            return await sync_to_async(
                QRCodeScan.objects.filter(
                    verification_code=verification_code
                ).first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения QR-кода по коду верификации: {e}")
    
    @staticmethod
    async def get_active_qr_codes() -> List[QRCodeScan]:
        """Получает все активные QR-коды."""
        try:
            return await sync_to_async(
                list
            )(
                QRCodeScan.objects.filter(
                    verification_code__is_used=False,
                    verification_code__expires_at__gt=timezone.now()
                ).select_related('verification_code').order_by('-created_at')
            )
        except Exception as e:
            raise DatabaseError(f"Ошибка получения активных QR-кодов: {e}")
    
    @staticmethod
    async def find_matching_qr_code(verification_code: str) -> Optional[QRCodeScan]:
        """Находит QR-код, соответствующий коду верификации."""
        try:
            # Получаем все активные QR-коды
            active_qr_codes = await QRCodeRepository.get_active_qr_codes()
            
            # Проверяем каждый QR-код на соответствие коду
            for qr_code in active_qr_codes:
                if qr_code.verification_code:
                    # Используем check_code_match для проверки без пометки как использованный
                    is_match = await sync_to_async(
                        qr_code.verification_code.check_code_match
                    )(verification_code)
                    
                    if is_match:
                        return qr_code
            
            return None
        except Exception as e:
            raise DatabaseError(f"Ошибка поиска соответствующего QR-кода: {e}")
    
    @staticmethod
    async def mark_bot_started(qr_code: QRCodeScan) -> None:
        """Отмечает запуск бота для QR-кода."""
        try:
            await sync_to_async(qr_code.mark_bot_started)()
        except Exception as e:
            raise DatabaseError(f"Ошибка отметки запуска бота для QR-кода: {e}")
    
    @staticmethod
    async def is_bot_started(qr_code: QRCodeScan) -> bool:
        """Проверяет, был ли запущен бот для QR-кода."""
        try:
            return qr_code.bot_started_at is not None
        except Exception as e:
            raise DatabaseError(f"Ошибка проверки запуска бота для QR-кода: {e}")
    
    @staticmethod
    async def get_qr_codes_by_chat_id(chat_id: str) -> List[QRCodeScan]:
        """Получает QR-коды по chat_id из связанного кода верификации."""
        try:
            return await sync_to_async(
                list
            )(
                QRCodeScan.objects.filter(
                    verification_code__telegram_chat_id=chat_id,
                    verification_code__verification_type='qr_registration',
                    verification_code__is_used=False,
                    verification_code__expires_at__gt=timezone.now()
                ).select_related('verification_code').order_by('-created_at')
            )
        except Exception as e:
            raise DatabaseError(f"Ошибка получения QR-кодов по chat_id: {e}")
    
    @staticmethod
    async def cleanup_expired_qr_codes() -> int:
        """Удаляет QR-коды с истекшими кодами верификации."""
        try:
            expired_qr_codes = QRCodeScan.objects.filter(
                verification_code__expires_at__lt=timezone.now()
            )
            count = await sync_to_async(expired_qr_codes.count)()
            await sync_to_async(expired_qr_codes.delete)()
            return count
        except Exception as e:
            raise DatabaseError(f"Ошибка очистки истекших QR-кодов: {e}")
    
    @staticmethod
    async def get_qr_code_stats() -> dict:
        """Получает статистику по QR-кодам."""
        try:
            total_count = await sync_to_async(
                QRCodeScan.objects.count
            )()
            
            active_count = await sync_to_async(
                QRCodeScan.objects.filter(
                    verification_code__is_used=False,
                    verification_code__expires_at__gt=timezone.now()
                ).count
            )()
            
            bot_started_count = await sync_to_async(
                QRCodeScan.objects.filter(
                    bot_started_at__isnull=False
                ).count
            )()
            
            return {
                'total': total_count,
                'active': active_count,
                'bot_started': bot_started_count,
                'expired': total_count - active_count
            }
        except Exception as e:
            raise DatabaseError(f"Ошибка получения статистики QR-кодов: {e}")