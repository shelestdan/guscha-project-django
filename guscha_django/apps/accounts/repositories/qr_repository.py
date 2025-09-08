from django.db import models
from django.utils import timezone
from django.db.models import Q, Count, Avg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid

from ..models import QRCodeScan, TelegramVerificationCode

logger = logging.getLogger(__name__)


class QRRepository:
    """Репозиторий для работы с QR-кодами"""
    
    def create_qr_code(self) -> QRCodeScan:
        """Создание нового QR-кода"""
        qr_code = QRCodeScan.objects.create()
        logger.info(f"Создан QR-код: {qr_code.qr_id}")
        return qr_code
    
    def get_by_id(self, qr_id: int) -> Optional[QRCodeScan]:
        """Получение QR-кода по ID"""
        try:
            return QRCodeScan.objects.get(id=qr_id)
        except QRCodeScan.DoesNotExist:
            return None
    
    def get_by_qr_id(self, qr_id: str) -> Optional[QRCodeScan]:
        """Получение QR-кода по qr_id (UUID)"""
        try:
            return QRCodeScan.objects.get(qr_id=qr_id)
        except QRCodeScan.DoesNotExist:
            return None
    
    def get_by_verification_code(self, verification_code: TelegramVerificationCode) -> Optional[QRCodeScan]:
        """Получение QR-кода по коду верификации"""
        try:
            return QRCodeScan.objects.get(verification_code=verification_code)
        except QRCodeScan.DoesNotExist:
            return None
    
    def update_qr_code(self, qr_code: QRCodeScan, **fields) -> QRCodeScan:
        """Обновление QR-кода"""
        for field, value in fields.items():
            if hasattr(qr_code, field):
                setattr(qr_code, field, value)
        qr_code.save()
        logger.info(f"Обновлен QR-код: {qr_code.qr_id}")
        return qr_code
    
    def mark_scanned(
        self,
        qr_code: QRCodeScan,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> QRCodeScan:
        """Отметка QR-кода как отсканированного"""
        qr_code.mark_scanned(ip_address, user_agent)
        logger.info(f"QR-код отмечен как отсканированный: {qr_code.qr_id}")
        return qr_code
    
    def mark_trigger_activated(self, qr_code: QRCodeScan) -> QRCodeScan:
        """Отметка активации триггера"""
        qr_code.mark_trigger_activated()
        logger.info(f"Триггер активирован для QR-кода: {qr_code.qr_id}")
        return qr_code
    
    def mark_bot_started(self, qr_code: QRCodeScan) -> QRCodeScan:
        """Отметка запуска бота"""
        qr_code.mark_bot_started()
        logger.info(f"Бот запущен для QR-кода: {qr_code.qr_id}")
        return qr_code
    
    def get_recent_qr_codes(self, limit: int = 10) -> models.QuerySet[QRCodeScan]:
        """Получение недавних QR-кодов"""
        return QRCodeScan.objects.order_by('-created_at')[:limit]
    
    def get_scanned_qr_codes(self) -> models.QuerySet[QRCodeScan]:
        """Получение отсканированных QR-кодов"""
        return QRCodeScan.objects.filter(scanned_at__isnull=False)
    
    def get_completed_qr_codes(self) -> models.QuerySet[QRCodeScan]:
        """Получение завершенных QR-кодов (полный поток)"""
        return QRCodeScan.objects.filter(
            scanned_at__isnull=False,
            trigger_activated_at__isnull=False,
            bot_started_at__isnull=False
        )
    
    def get_qr_codes_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> models.QuerySet[QRCodeScan]:
        """Получение QR-кодов за период"""
        return QRCodeScan.objects.filter(
            created_at__range=(start_date, end_date)
        )
    
    def get_qr_statistics(self) -> Dict[str, Any]:
        """Получение статистики QR-кодов"""
        total_qr_codes = QRCodeScan.objects.count()
        scanned_qr_codes = QRCodeScan.objects.filter(
            scanned_at__isnull=False
        ).count()
        triggered_qr_codes = QRCodeScan.objects.filter(
            trigger_activated_at__isnull=False
        ).count()
        bot_started_qr_codes = QRCodeScan.objects.filter(
            bot_started_at__isnull=False
        ).count()
        completed_qr_codes = QRCodeScan.objects.filter(
            scanned_at__isnull=False,
            trigger_activated_at__isnull=False,
            bot_started_at__isnull=False
        ).count()
        
        # Статистика за последние 24 часа
        last_24h = timezone.now() - timedelta(hours=24)
        qr_codes_last_24h = QRCodeScan.objects.filter(
            created_at__gte=last_24h
        ).count()
        scanned_last_24h = QRCodeScan.objects.filter(
            scanned_at__gte=last_24h
        ).count()
        
        # Средняя статистика сканирований
        avg_scan_count = QRCodeScan.objects.aggregate(
            avg_scans=Avg('scan_count')
        )['avg_scans'] or 0
        
        avg_activations = QRCodeScan.objects.aggregate(
            avg_activations=Avg('successful_activations')
        )['avg_activations'] or 0
        
        # Коэффициенты конверсии
        scan_rate = (scanned_qr_codes / total_qr_codes * 100) if total_qr_codes > 0 else 0
        trigger_rate = (triggered_qr_codes / scanned_qr_codes * 100) if scanned_qr_codes > 0 else 0
        bot_start_rate = (bot_started_qr_codes / triggered_qr_codes * 100) if triggered_qr_codes > 0 else 0
        completion_rate = (completed_qr_codes / total_qr_codes * 100) if total_qr_codes > 0 else 0
        
        return {
            'total_qr_codes': total_qr_codes,
            'scanned_qr_codes': scanned_qr_codes,
            'triggered_qr_codes': triggered_qr_codes,
            'bot_started_qr_codes': bot_started_qr_codes,
            'completed_qr_codes': completed_qr_codes,
            'qr_codes_last_24h': qr_codes_last_24h,
            'scanned_last_24h': scanned_last_24h,
            'avg_scan_count': round(avg_scan_count, 2),
            'avg_activations': round(avg_activations, 2),
            'scan_rate': round(scan_rate, 2),
            'trigger_rate': round(trigger_rate, 2),
            'bot_start_rate': round(bot_start_rate, 2),
            'completion_rate': round(completion_rate, 2)
        }
    
    def cleanup_old_qr_codes(self, days: int = 7) -> int:
        """Очистка старых QR-кодов"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Удаляем только незавершенные QR-коды старше указанного периода
        deleted_count, _ = QRCodeScan.objects.filter(
            created_at__lt=cutoff_date,
            bot_started_at__isnull=True  # Не завершенные
        ).delete()
        
        logger.info(f"Удалено старых QR-кодов: {deleted_count}")
        return deleted_count
    
    def cleanup_unused_qr_codes(self, hours: int = 2) -> int:
        """Очистка неиспользованных QR-кодов"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Удаляем QR-коды, которые не были отсканированы в течение указанного времени
        deleted_count, _ = QRCodeScan.objects.filter(
            created_at__lt=cutoff_time,
            scanned_at__isnull=True
        ).delete()
        
        logger.info(f"Удалено неиспользованных QR-кодов: {deleted_count}")
        return deleted_count
    
    def get_qr_codes_with_verification(self) -> models.QuerySet[QRCodeScan]:
        """Получение QR-кодов с кодами верификации"""
        return QRCodeScan.objects.filter(
            verification_code__isnull=False
        ).select_related('verification_code')
    
    def get_qr_codes_by_ip(self, ip_address: str) -> models.QuerySet[QRCodeScan]:
        """Получение QR-кодов по IP-адресу"""
        return QRCodeScan.objects.filter(
            scan_ip_address=ip_address
        ).order_by('-scanned_at')
    
    def get_popular_qr_codes(self, limit: int = 10) -> models.QuerySet[QRCodeScan]:
        """Получение популярных QR-кодов (по количеству сканирований)"""
        return QRCodeScan.objects.filter(
            scan_count__gt=0
        ).order_by('-scan_count')[:limit]
    
    def get_successful_qr_codes(self, limit: int = 10) -> models.QuerySet[QRCodeScan]:
        """Получение успешных QR-кодов (по количеству активаций)"""
        return QRCodeScan.objects.filter(
            successful_activations__gt=0
        ).order_by('-successful_activations')[:limit]
    
    def search_qr_codes(self, query: str) -> models.QuerySet[QRCodeScan]:
        """Поиск QR-кодов"""
        return QRCodeScan.objects.filter(
            Q(qr_id__icontains=query) |
            Q(scan_ip_address__icontains=query) |
            Q(scan_user_agent__icontains=query)
        )
    
    def get_qr_codes_needing_cleanup(self, days: int = 30) -> models.QuerySet[QRCodeScan]:
        """Получение QR-кодов, требующих очистки"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return QRCodeScan.objects.filter(
            created_at__lt=cutoff_date,
            successful_activations=0
        )
    
    def bulk_update_qr_codes(self, qr_codes: List[QRCodeScan], fields: List[str]) -> None:
        """Массовое обновление QR-кодов"""
        QRCodeScan.objects.bulk_update(qr_codes, fields)
        logger.info(f"Массово обновлено QR-кодов: {len(qr_codes)}")
    
    def exists_by_qr_id(self, qr_id: str) -> bool:
        """Проверка существования QR-кода по qr_id"""
        return QRCodeScan.objects.filter(qr_id=qr_id).exists()
    
    def get_optimized_queryset(self) -> models.QuerySet[QRCodeScan]:
        """Получение оптимизированного QuerySet для QR-кодов"""
        return QRCodeScan.objects.select_related('verification_code')
    
    def bulk_process_qr_codes(self, chunk_size: int = 1000) -> models.QuerySet[QRCodeScan]:
        """Обработка QR-кодов по частям для экономии памяти"""
        queryset = QRCodeScan.objects.all().select_related('verification_code').order_by('id')
        
        # Используем iterator() для экономии памяти
        for qr_code in queryset.iterator(chunk_size=chunk_size):
            yield qr_code
    
    def bulk_process_scanned_qr_codes(self, chunk_size: int = 1000) -> models.QuerySet[QRCodeScan]:
        """Обработка отсканированных QR-кодов по частям"""
        queryset = QRCodeScan.objects.filter(
            scanned_at__isnull=False
        ).select_related('verification_code').order_by('id')
        
        for qr_code in queryset.iterator(chunk_size=chunk_size):
            yield qr_code
    
    def bulk_update_qr_codes_in_chunks(self, updates_data: List[tuple], chunk_size: int = 500) -> None:
        """Массовое обновление QR-кодов по частям"""
        from django.db import transaction
        
        # Разбиваем на чанки
        for i in range(0, len(updates_data), chunk_size):
            chunk = updates_data[i:i + chunk_size]
            
            with transaction.atomic():
                qr_codes_to_update = []
                qr_ids = [item[0] for item in chunk]
                
                # Получаем QR-коды для обновления
                qr_codes = QRCodeScan.objects.filter(id__in=qr_ids)
                
                for qr_code in qr_codes:
                    # Находим соответствующие данные для обновления
                    for qr_id, update_fields in chunk:
                        if qr_code.id == qr_id:
                            for field, value in update_fields.items():
                                setattr(qr_code, field, value)
                            qr_codes_to_update.append(qr_code)
                            break
                
                # Массовое обновление
                if qr_codes_to_update:
                    QRCodeScan.objects.bulk_update(
                        qr_codes_to_update, 
                        list(update_fields.keys())
                    )
                    logger.info(f"Массово обновлено QR-кодов в чанке: {len(qr_codes_to_update)}")
    
    def get_qr_codes_for_export(self, chunk_size: int = 2000) -> models.QuerySet[QRCodeScan]:
        """Получение QR-кодов для экспорта с минимальным использованием памяти"""
        queryset = QRCodeScan.objects.all().select_related(
            'verification_code'
        ).order_by('id')
        
        # Используем iterator для больших объемов данных
        for qr_code in queryset.iterator(chunk_size=chunk_size):
            yield qr_code
    
    def get_qr_conversion_funnel(self) -> Dict[str, Any]:
        """Получение воронки конверсии QR-кодов"""
        total = QRCodeScan.objects.count()
        if total == 0:
            return {
                'total_created': 0,
                'scanned': 0,
                'triggered': 0,
                'bot_started': 0,
                'completed': 0,
                'conversion_rates': {
                    'scan_rate': 0,
                    'trigger_rate': 0,
                    'bot_start_rate': 0,
                    'completion_rate': 0
                }
            }
        
        scanned = QRCodeScan.objects.filter(scanned_at__isnull=False).count()
        triggered = QRCodeScan.objects.filter(trigger_activated_at__isnull=False).count()
        bot_started = QRCodeScan.objects.filter(bot_started_at__isnull=False).count()
        completed = QRCodeScan.objects.filter(
            scanned_at__isnull=False,
            trigger_activated_at__isnull=False,
            bot_started_at__isnull=False
        ).count()
        
        return {
            'total_created': total,
            'scanned': scanned,
            'triggered': triggered,
            'bot_started': bot_started,
            'completed': completed,
            'conversion_rates': {
                'scan_rate': round((scanned / total * 100), 2),
                'trigger_rate': round((triggered / scanned * 100), 2) if scanned > 0 else 0,
                'bot_start_rate': round((bot_started / triggered * 100), 2) if triggered > 0 else 0,
                'completion_rate': round((completed / total * 100), 2)
            }
        }