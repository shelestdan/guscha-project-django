from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Avg
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from ..models import PendingUserRegistration

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    def get_by_telegram_chat_id(self, telegram_chat_id: str) -> Optional[User]:
        """Получение пользователя по Telegram chat ID"""
        try:
            return User.objects.get(telegram_chat_id=telegram_chat_id)
        except User.DoesNotExist:
            return None
    
    def get_by_phone(self, phone: str) -> Optional[User]:
        """Получение пользователя по номеру телефона"""
        try:
            return User.objects.get(phone=phone)
        except User.DoesNotExist:
            return None
    
    def create_user(
        self, 
        email: str, 
        password: str = None, 
        first_name: str = '', 
        last_name: str = '',
        skip_password: bool = False,
        **extra_fields
    ) -> User:
        """Создание нового пользователя"""
        if skip_password or password is None:
            # Для OAuth пользователей создаем пользователя без пароля
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                **extra_fields
            )
            user.set_unusable_password()
            user.save()
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                **extra_fields
            )
        logger.info(f"Создан пользователь: {user.email} (OAuth: {skip_password})")
        return user
    
    def create_superuser(
        self, 
        email: str, 
        password: str, 
        first_name: str = '', 
        last_name: str = '',
        **extra_fields
    ) -> User:
        """Создание суперпользователя"""
        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        logger.info(f"Создан суперпользователь: {user.email}")
        return user
    
    def update_user(self, user: User, **fields) -> User:
        """Обновление данных пользователя"""
        for field, value in fields.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.save()
        logger.info(f"Обновлен пользователь: {user.email}")
        return user
    
    def set_password(self, user: User, password: str) -> User:
        """Установка пароля пользователя"""
        user.set_password(password)
        user.save()
        logger.info(f"Пароль изменен для пользователя: {user.email}")
        return user
    
    def deactivate_user(self, user: User) -> User:
        """Деактивация пользователя"""
        user.is_active = False
        user.save()
        logger.info(f"Деактивирован пользователь: {user.email}")
        return user
    
    def activate_user(self, user: User) -> User:
        """Активация пользователя"""
        user.is_active = True
        user.save()
        logger.info(f"Активирован пользователь: {user.email}")
        return user
    
    def link_telegram(self, user: User, telegram_chat_id: str, telegram_username: str = '') -> User:
        """Привязка Telegram к пользователю"""
        user.telegram_chat_id = telegram_chat_id
        if telegram_username:
            user.telegram_username = telegram_username
        user.save()
        logger.info(f"Telegram привязан к пользователю: {user.email}")
        return user
    
    def unlink_telegram(self, user: User) -> User:
        """Отвязка Telegram от пользователя"""
        user.telegram_chat_id = None
        user.telegram_username = ''
        user.save()
        logger.info(f"Telegram отвязан от пользователя: {user.email}")
        return user
    
    def get_active_users(self) -> models.QuerySet[User]:
        """Получение активных пользователей"""
        return User.objects.filter(is_active=True)
    
    def get_users_with_telegram(self) -> models.QuerySet[User]:
        """Получение пользователей с привязанным Telegram"""
        return User.objects.filter(
            telegram_chat_id__isnull=False,
            telegram_chat_id__gt=''
        )
    
    def search_users(self, query: str) -> models.QuerySet[User]:
        """Поиск пользователей по email, имени или фамилии"""
        return User.objects.filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Получение статистики пользователей"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        users_with_telegram = User.objects.filter(
            telegram_chat_id__isnull=False,
            telegram_chat_id__gt=''
        ).count()
        
        # Статистика по датам регистрации
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        new_users_today = User.objects.filter(date_joined__date=today).count()
        new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
        new_users_month = User.objects.filter(date_joined__date__gte=month_ago).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'users_with_telegram': users_with_telegram,
            'telegram_integration_rate': (
                (users_with_telegram / total_users * 100) if total_users > 0 else 0
            ),
            'new_users_today': new_users_today,
            'new_users_week': new_users_week,
            'new_users_month': new_users_month
        }
    
    def get_recent_users(self, limit: int = 10) -> models.QuerySet[User]:
        """Получение недавно зарегистрированных пользователей"""
        return User.objects.order_by('-date_joined')[:limit]
    
    def bulk_update_users(self, users: List[User], fields: List[str]) -> None:
        """Массовое обновление пользователей"""
        User.objects.bulk_update(users, fields)
        logger.info(f"Массово обновлено пользователей: {len(users)}")
    
    def delete_inactive_users(self, days: int = 365) -> int:
        """Удаление неактивных пользователей"""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = User.objects.filter(
            is_active=False,
            last_login__lt=cutoff_date
        ).delete()
        logger.info(f"Удалено неактивных пользователей: {deleted_count}")
        return deleted_count
    
    # Методы для работы с ожидающими регистрациями
    
    def create_pending_registration(
        self, 
        email: str, 
        first_name: str = '', 
        last_name: str = '',
        **extra_data
    ) -> PendingUserRegistration:
        """Создание ожидающей регистрации"""
        pending_registration = PendingUserRegistration.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            extra_data=extra_data
        )
        logger.info(f"Создана ожидающая регистрация: {email}")
        return pending_registration
    
    def get_pending_registration_by_id(self, registration_id: int) -> Optional[PendingUserRegistration]:
        """Получение ожидающей регистрации по ID"""
        try:
            return PendingUserRegistration.objects.get(id=registration_id)
        except PendingUserRegistration.DoesNotExist:
            return None
    
    def get_pending_registration_by_email(self, email: str) -> Optional[PendingUserRegistration]:
        """Получение ожидающей регистрации по email"""
        try:
            return PendingUserRegistration.objects.get(email=email)
        except PendingUserRegistration.DoesNotExist:
            return None
    
    def create_user_from_pending(self, pending_registration: PendingUserRegistration) -> User:
        """Создание пользователя из ожидающей регистрации"""
        # Проверяем, что пользователь еще не существует
        existing_user = self.get_by_email(pending_registration.email)
        if existing_user:
            logger.warning(f"Пользователь с email {pending_registration.email} уже существует")
            return existing_user
        
        # Создаем нового пользователя
        user = User(
            email=pending_registration.email,
            first_name=pending_registration.first_name,
            last_name=pending_registration.last_name,
            phone=pending_registration.phone,
            address=pending_registration.address,
            is_active=True,
            is_telegram_verified=True  # Верифицирован через Telegram при QR-регистрации
        )
        
        # Устанавливаем пароль из хэша
        user.password = pending_registration.password_hash
        user.save()
        
        logger.info(f"Создан пользователь из ожидающей регистрации: {user.email}")
        return user
    
    def complete_pending_registration(
        self, 
        pending_registration: PendingUserRegistration,
        password: str,
        **extra_fields
    ) -> User:
        """Завершение ожидающей регистрации"""
        user = self.create_user(
            email=pending_registration.email,
            password=password,
            first_name=pending_registration.first_name,
            last_name=pending_registration.last_name,
            **extra_fields
        )
        
        # Удаление ожидающей регистрации
        pending_registration.delete()
        
        logger.info(f"Завершена ожидающая регистрация: {user.email}")
        return user
    
    def cleanup_expired_pending_registrations(self, hours: int = 24) -> int:
        """Очистка просроченных ожидающих регистраций"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        deleted_count, _ = PendingUserRegistration.objects.filter(
            created_at__lt=cutoff_time
        ).delete()
        logger.info(f"Удалено просроченных ожидающих регистраций: {deleted_count}")
        return deleted_count
    
    def get_optimized_queryset(self) -> models.QuerySet[User]:
        """Получение оптимизированного QuerySet для пользователей"""
        return User.objects.select_related().prefetch_related()
    
    def bulk_process_users(self, chunk_size: int = 1000) -> models.QuerySet[User]:
        """Обработка пользователей по частям для экономии памяти"""
        queryset = User.objects.filter(is_active=True).order_by('id')
        
        # Используем iterator() для экономии памяти
        for user in queryset.iterator(chunk_size=chunk_size):
            yield user
    
    def bulk_process_all_users(self, chunk_size: int = 1000) -> models.QuerySet[User]:
        """Обработка всех пользователей по частям"""
        queryset = User.objects.all().order_by('id')
        
        for user in queryset.iterator(chunk_size=chunk_size):
            yield user
    
    def bulk_update_users_in_chunks(self, updates_data: List[tuple], chunk_size: int = 500) -> None:
        """Массовое обновление пользователей по частям"""
        from django.db import transaction
        
        # Разбиваем на чанки
        for i in range(0, len(updates_data), chunk_size):
            chunk = updates_data[i:i + chunk_size]
            
            with transaction.atomic():
                users_to_update = []
                user_ids = [item[0] for item in chunk]
                
                # Получаем пользователей для обновления
                users = User.objects.filter(id__in=user_ids)
                
                for user in users:
                    # Находим соответствующие данные для обновления
                    for user_id, update_fields in chunk:
                        if user.id == user_id:
                            for field, value in update_fields.items():
                                setattr(user, field, value)
                            users_to_update.append(user)
                            break
                
                # Массовое обновление
                if users_to_update:
                    User.objects.bulk_update(
                        users_to_update, 
                        list(update_fields.keys())
                    )
                    logger.info(f"Массово обновлено пользователей в чанке: {len(users_to_update)}")
    
    def get_users_for_export(self, chunk_size: int = 2000) -> models.QuerySet[User]:
        """Получение пользователей для экспорта с минимальным использованием памяти"""
        queryset = User.objects.all().order_by('id')
        
        # Используем iterator для больших объемов данных
        for user in queryset.iterator(chunk_size=chunk_size):
            yield user
    
    def exists_by_email(self, email: str) -> bool:
        """Проверка существования пользователя по email"""
        return User.objects.filter(email=email).exists()
    
    def exists_by_telegram_chat_id(self, telegram_chat_id: str) -> bool:
        """Проверка существования пользователя по Telegram chat ID"""
        return User.objects.filter(telegram_chat_id=telegram_chat_id).exists()
    
    def update_last_login(self, user: User) -> User:
        """Обновление времени последнего входа пользователя"""
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return user