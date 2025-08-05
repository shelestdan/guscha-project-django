from django.db import models
from django.utils import timezone
from django.db.models import Q, Count
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..models import TelegramVerificationCode

logger = logging.getLogger(__name__)


class TelegramRepository:
    """Репозиторий для работы с Telegram данными"""
    
    def create_verification_code(
        self,
        telegram_chat_id: Optional[str],
        verification_type: str,
        code: str,
        expires_at: datetime,
        user=None,
        pending_registration=None,
        telegram_phone=None
    ) -> TelegramVerificationCode:
        """Создание кода верификации"""
        logger.info(f"Начало создания кода верификации: chat_id='{telegram_chat_id}', type={verification_type}, expires_at={expires_at}")
        
        # Преобразуем пустую строку в None для nullable поля
        original_chat_id = telegram_chat_id
        if telegram_chat_id is None or telegram_chat_id == '' or telegram_chat_id == '0':
            telegram_chat_id = None
        elif isinstance(telegram_chat_id, str) and telegram_chat_id.isdigit():
            telegram_chat_id = int(telegram_chat_id)
        else:
            telegram_chat_id = None
        
        logger.info(f"Преобразование chat_id: '{original_chat_id}' -> {telegram_chat_id}")
        
        verification_code = TelegramVerificationCode.objects.create(
            telegram_chat_id=telegram_chat_id,
            verification_type=verification_type,
            code=code,
            expires_at=expires_at,
            user=user,
            pending_registration=pending_registration,
            telegram_phone=telegram_phone
        )
        
        logger.info(f"Код верификации создан в БД: ID={verification_code.id}, chat_id={verification_code.telegram_chat_id}, expires_at={verification_code.expires_at}, type={verification_code.verification_type}")
        return verification_code
    
    def get_verification_code(
        self,
        telegram_chat_id: str,
        code: str,
        verification_type: str
    ) -> Optional[TelegramVerificationCode]:
        """Получение кода верификации"""
        try:
            codes = TelegramVerificationCode.objects.filter(
                telegram_chat_id=telegram_chat_id,
                verification_type=verification_type,
                is_used=False
            )
            # Проверяем каждый код с помощью verify_code
            for verification_code in codes:
                if verification_code.verify_code(code):
                    return verification_code
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении кода верификации: {e}")
            return None
    
    def get_active_verification_code(
        self,
        telegram_chat_id: str,
        code: str,
        verification_type: str
    ) -> Optional[TelegramVerificationCode]:
        """Получение активного кода верификации"""
        try:
            # Для QR-регистрации ищем код без привязки к chat_id
            if verification_type == 'qr_registration':
                codes = TelegramVerificationCode.objects.filter(
                    verification_type=verification_type,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                # Проверяем каждый код с помощью verify_code
                for verification_code in codes:
                    if verification_code.verify_code(code):
                        return verification_code
                return None
            else:
                codes = TelegramVerificationCode.objects.filter(
                    telegram_chat_id=telegram_chat_id,
                    verification_type=verification_type,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                # Проверяем каждый код с помощью verify_code
                for verification_code in codes:
                    if verification_code.verify_code(code):
                        return verification_code
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении активного кода верификации: {e}")
            return None
    
    def get_latest_verification_code(
        self,
        telegram_chat_id: str,
        verification_type: str
    ) -> Optional[TelegramVerificationCode]:
        """Получение последнего кода верификации"""
        try:
            return TelegramVerificationCode.objects.filter(
                telegram_chat_id=telegram_chat_id,
                verification_type=verification_type
            ).order_by('-created_at').first()
        except TelegramVerificationCode.DoesNotExist:
            return None
    
    def mark_code_as_used(self, verification_code: TelegramVerificationCode) -> TelegramVerificationCode:
        """Отметка кода как использованного"""
        verification_code.is_used = True
        verification_code.used_at = timezone.now()
        verification_code.save()
        logger.info(f"Код верификации отмечен как использованный: ID {verification_code.id}")
        return verification_code
    
    def get_active_codes_for_chat(
        self,
        telegram_chat_id: str,
        verification_type: Optional[str] = None
    ) -> models.QuerySet[TelegramVerificationCode]:
        """Получение активных кодов для чата"""
        queryset = TelegramVerificationCode.objects.filter(
            telegram_chat_id=telegram_chat_id,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        if verification_type:
            queryset = queryset.filter(verification_type=verification_type)
        
        return queryset.order_by('-created_at')
    
    def cleanup_expired_codes(self) -> int:
        """Очистка просроченных кодов"""
        deleted_count, _ = TelegramVerificationCode.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        logger.info(f"Удалено просроченных кодов верификации: {deleted_count}")
        return deleted_count
    
    def cleanup_used_codes(self, days: int = 7) -> int:
        """Очистка использованных кодов старше указанного количества дней"""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = TelegramVerificationCode.objects.filter(
            is_used=True,
            used_at__lt=cutoff_date
        ).delete()
        logger.info(f"Удалено использованных кодов верификации: {deleted_count}")
        return deleted_count
    
    def get_verification_attempts(
        self,
        telegram_chat_id: str,
        verification_type: str,
        hours: int = 1
    ) -> int:
        """Получение количества попыток верификации за указанное время"""
        since = timezone.now() - timedelta(hours=hours)
        return TelegramVerificationCode.objects.filter(
            telegram_chat_id=telegram_chat_id,
            verification_type=verification_type,
            created_at__gte=since
        ).count()
    
    def get_failed_verification_attempts(
        self,
        telegram_chat_id: str,
        verification_type: str,
        hours: int = 1
    ) -> int:
        """Получение количества неудачных попыток верификации"""
        since = timezone.now() - timedelta(hours=hours)
        
        # Считаем коды, которые истекли или были созданы, но не использованы
        expired_codes = TelegramVerificationCode.objects.filter(
            telegram_chat_id=telegram_chat_id,
            verification_type=verification_type,
            created_at__gte=since,
            expires_at__lt=timezone.now(),
            is_used=False
        ).count()
        
        return expired_codes
    
    def invalidate_codes_for_chat(
        self,
        telegram_chat_id: str,
        verification_type: Optional[str] = None
    ) -> int:
        """Аннулирование всех активных кодов для чата"""
        queryset = TelegramVerificationCode.objects.filter(
            telegram_chat_id=telegram_chat_id,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        if verification_type:
            queryset = queryset.filter(verification_type=verification_type)
        
        # Помечаем как использованные вместо удаления для аудита
        updated_count = queryset.update(
            is_used=True,
            used_at=timezone.now()
        )
        
        logger.info(f"Аннулировано кодов верификации: {updated_count}")
        return updated_count
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """Получение статистики верификации"""
        total_codes = TelegramVerificationCode.objects.count()
        used_codes = TelegramVerificationCode.objects.filter(is_used=True).count()
        expired_codes = TelegramVerificationCode.objects.filter(
            expires_at__lt=timezone.now(),
            is_used=False
        ).count()
        active_codes = TelegramVerificationCode.objects.filter(
            expires_at__gt=timezone.now(),
            is_used=False
        ).count()
        
        # Статистика по типам верификации
        verification_types = TelegramVerificationCode.objects.values(
            'verification_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Статистика за последние 24 часа
        last_24h = timezone.now() - timedelta(hours=24)
        codes_last_24h = TelegramVerificationCode.objects.filter(
            created_at__gte=last_24h
        ).count()
        
        success_rate = (used_codes / total_codes * 100) if total_codes > 0 else 0
        
        return {
            'total_codes': total_codes,
            'used_codes': used_codes,
            'expired_codes': expired_codes,
            'active_codes': active_codes,
            'success_rate': round(success_rate, 2),
            'codes_last_24h': codes_last_24h,
            'verification_types': list(verification_types)
        }
    
    def get_codes_by_type(self, verification_type: str) -> models.QuerySet[TelegramVerificationCode]:
        """Получение кодов по типу верификации"""
        return TelegramVerificationCode.objects.filter(
            verification_type=verification_type
        ).order_by('-created_at')
    
    def get_recent_codes(
        self,
        limit: int = 10,
        telegram_chat_id: Optional[str] = None
    ) -> models.QuerySet[TelegramVerificationCode]:
        """Получение недавних кодов верификации"""
        queryset = TelegramVerificationCode.objects.all()
        
        if telegram_chat_id:
            queryset = queryset.filter(telegram_chat_id=telegram_chat_id)
        
        return queryset.order_by('-created_at')[:limit]
    
    def exists_active_code(
        self,
        telegram_chat_id: str,
        verification_type: str
    ) -> bool:
        """Проверка существования активного кода"""
        return TelegramVerificationCode.objects.filter(
            telegram_chat_id=telegram_chat_id,
            verification_type=verification_type,
            is_used=False,
            expires_at__gt=timezone.now()
        ).exists()
    
    def get_code_by_id(self, code_id: int) -> Optional[TelegramVerificationCode]:
        """Получение кода по ID"""
        try:
            return TelegramVerificationCode.objects.get(id=code_id)
        except TelegramVerificationCode.DoesNotExist:
            return None
    
    def bulk_cleanup_codes(self, chat_ids: List[str]) -> int:
        """Массовая очистка кодов для списка чатов"""
        deleted_count, _ = TelegramVerificationCode.objects.filter(
            telegram_chat_id__in=chat_ids
        ).delete()
        logger.info(f"Массово удалено кодов верификации: {deleted_count}")
        return deleted_count
    
    def get_unique_chat_ids(self) -> List[str]:
        """Получение уникальных chat_id"""
        return list(
            TelegramVerificationCode.objects.values_list(
                'telegram_chat_id', flat=True
            ).distinct()
        )
    
    def get_verification_history(
        self,
        telegram_chat_id: str,
        days: int = 30
    ) -> models.QuerySet[TelegramVerificationCode]:
        """Получение истории верификации для чата"""
        since = timezone.now() - timedelta(days=days)
        return TelegramVerificationCode.objects.filter(
            telegram_chat_id=telegram_chat_id,
            created_at__gte=since
        ).order_by('-created_at')
    
    def deactivate_old_codes(
        self,
        telegram_chat_id: Optional[str],
        verification_type: str,
        exclude_code_id: Optional[int] = None
    ) -> int:
        """Деактивация старых кодов верификации"""
        queryset = TelegramVerificationCode.objects.filter(
            verification_type=verification_type,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        # Исключаем текущий создаваемый код
        if exclude_code_id:
            queryset = queryset.exclude(id=exclude_code_id)
        
        # Для QR-кодов chat_id может быть None или пустым
        if telegram_chat_id:
            queryset = queryset.filter(telegram_chat_id=telegram_chat_id)
        else:
            # Для QR-кодов деактивируем коды с пустым chat_id
            queryset = queryset.filter(telegram_chat_id__isnull=True)
        
        updated_count = queryset.update(
            is_used=True,
            used_at=timezone.now()
        )
        
        logger.info(f"Деактивировано старых кодов: {updated_count}")
        return updated_count
    
    def deactivate_all_user_codes(self, user) -> int:
        """Деактивация всех кодов верификации пользователя"""
        updated_count = TelegramVerificationCode.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now()
        ).update(
            is_used=True,
            used_at=timezone.now()
        )
        
        logger.info(f"Деактивировано кодов пользователя {user.email}: {updated_count}")
        return updated_count