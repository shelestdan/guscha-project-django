from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password, ValidationError as PasswordValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone
from django.db import models
from django.db.models import Q
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthRepository:
    """Репозиторий для работы с аутентификацией"""
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            user = authenticate(username=email, password=password)
            if user and user.is_active:
                logger.info(f"Успешная аутентификация пользователя: {email}")
                return user
            else:
                logger.warning(f"Неудачная аутентификация пользователя: {email}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при аутентификации пользователя {email}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        try:
            return User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        try:
            return User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return None
    
    def update_last_login(self, user: User) -> User:
        """Обновление времени последнего входа"""
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        logger.info(f"Обновлено время последнего входа для пользователя: {user.email}")
        return user
    
    def check_password(self, user: User, password: str) -> bool:
        """Проверка пароля пользователя"""
        return user.check_password(password)
    
    def set_password(self, user: User, password: str) -> User:
        """Установка нового пароля"""
        try:
            validate_password(password, user=user)
        except PasswordValidationError as e:
            raise ValueError(str(e))
        user.set_password(password)
        user.save()
        logger.info(f"Пароль изменен для пользователя: {user.email}")
        return user
    
    def generate_password_reset_token(self, user: User) -> str:
        """Генерация токена для сброса пароля"""
        token = default_token_generator.make_token(user)
        logger.info(f"Сгенерирован токен сброса пароля для пользователя: {user.email}")
        return token
    
    def verify_password_reset_token(self, user: User, token: str) -> bool:
        """Проверка токена сброса пароля"""
        is_valid = default_token_generator.check_token(user, token)
        if is_valid:
            logger.info(f"Токен сброса пароля подтвержден для пользователя: {user.email}")
        else:
            logger.warning(f"Недействительный токен сброса пароля для пользователя: {user.email}")
        return is_valid
    
    def generate_uid_from_user(self, user: User) -> str:
        """Генерация UID из пользователя для сброса пароля"""
        return urlsafe_base64_encode(force_bytes(user.pk))
    
    def get_user_from_uid(self, uid: str) -> Optional[User]:
        """Получение пользователя из UID"""
        try:
            user_id = urlsafe_base64_decode(uid).decode()
            return User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
    
    def is_user_active(self, user: User) -> bool:
        """Проверка активности пользователя"""
        return user.is_active
    
    def activate_user(self, user: User) -> User:
        """Активация пользователя"""
        user.is_active = True
        user.save(update_fields=['is_active'])
        logger.info(f"Пользователь активирован: {user.email}")
        return user
    
    def deactivate_user(self, user: User) -> User:
        """Деактивация пользователя"""
        user.is_active = False
        user.save(update_fields=['is_active'])
        logger.info(f"Пользователь деактивирован: {user.email}")
        return user
    
    def get_users_by_last_login(
        self, 
        days_ago: int = 30
    ) -> models.QuerySet[User]:
        """Получение пользователей по времени последнего входа"""
        cutoff_date = timezone.now() - timedelta(days=days_ago)
        return User.objects.filter(
            last_login__gte=cutoff_date,
            is_active=True
        ).order_by('-last_login')
    
    def get_inactive_users(
        self, 
        days_ago: int = 90
    ) -> models.QuerySet[User]:
        """Получение неактивных пользователей"""
        cutoff_date = timezone.now() - timedelta(days=days_ago)
        return User.objects.filter(
            Q(last_login__lt=cutoff_date) | Q(last_login__isnull=True),
            is_active=True
        )
    
    def get_recently_registered_users(
        self, 
        days: int = 7
    ) -> models.QuerySet[User]:
        """Получение недавно зарегистрированных пользователей"""
        since = timezone.now() - timedelta(days=days)
        return User.objects.filter(
            date_joined__gte=since,
            is_active=True
        ).order_by('-date_joined')
    
    def get_auth_statistics(self) -> Dict[str, Any]:
        """Получение статистики аутентификации"""
        total_users = User.objects.filter(is_active=True).count()
        
        # Статистика по времени последнего входа
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)
        
        active_last_24h = User.objects.filter(
            last_login__gte=last_24h,
            is_active=True
        ).count()
        
        active_last_week = User.objects.filter(
            last_login__gte=last_week,
            is_active=True
        ).count()
        
        active_last_month = User.objects.filter(
            last_login__gte=last_month,
            is_active=True
        ).count()
        
        # Пользователи, которые никогда не входили
        never_logged_in = User.objects.filter(
            last_login__isnull=True,
            is_active=True
        ).count()
        
        # Новые регистрации
        new_registrations_24h = User.objects.filter(
            date_joined__gte=last_24h,
            is_active=True
        ).count()
        
        new_registrations_week = User.objects.filter(
            date_joined__gte=last_week,
            is_active=True
        ).count()
        
        # Коэффициенты активности
        activity_rate_24h = (active_last_24h / total_users * 100) if total_users > 0 else 0
        activity_rate_week = (active_last_week / total_users * 100) if total_users > 0 else 0
        activity_rate_month = (active_last_month / total_users * 100) if total_users > 0 else 0
        
        return {
            'total_active_users': total_users,
            'active_last_24h': active_last_24h,
            'active_last_week': active_last_week,
            'active_last_month': active_last_month,
            'never_logged_in': never_logged_in,
            'new_registrations_24h': new_registrations_24h,
            'new_registrations_week': new_registrations_week,
            'activity_rates': {
                'daily': round(activity_rate_24h, 2),
                'weekly': round(activity_rate_week, 2),
                'monthly': round(activity_rate_month, 2)
            }
        }
    
    def search_users_by_email(self, email_query: str) -> models.QuerySet[User]:
        """Поиск пользователей по email"""
        return User.objects.filter(
            email__icontains=email_query,
            is_active=True
        ).order_by('email')
    
    def get_users_requiring_password_reset(
        self, 
        days_since_last_change: int = 90
    ) -> models.QuerySet[User]:
        """Получение пользователей, которым требуется смена пароля"""
        # Примечание: Django не отслеживает дату последней смены пароля по умолчанию
        # Это можно реализовать через дополнительное поле в модели пользователя
        cutoff_date = timezone.now() - timedelta(days=days_since_last_change)
        return User.objects.filter(
            date_joined__lt=cutoff_date,
            is_active=True
        )
    
    def bulk_deactivate_users(self, user_ids: list) -> int:
        """Массовая деактивация пользователей"""
        updated_count = User.objects.filter(
            id__in=user_ids,
            is_active=True
        ).update(is_active=False)
        
        logger.info(f"Массово деактивировано пользователей: {updated_count}")
        return updated_count
    
    def bulk_activate_users(self, user_ids: list) -> int:
        """Массовая активация пользователей"""
        updated_count = User.objects.filter(
            id__in=user_ids,
            is_active=False
        ).update(is_active=True)
        
        logger.info(f"Массово активировано пользователей: {updated_count}")
        return updated_count
    
    def get_user_login_history(
        self, 
        user: User, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Получение истории входов пользователя"""
        # Примечание: Django не ведет подробную историю входов по умолчанию
        # Это требует дополнительной реализации через middleware или сигналы
        return {
            'user_id': user.id,
            'email': user.email,
            'last_login': user.last_login,
            'date_joined': user.date_joined,
            'is_active': user.is_active,
            'note': 'Подробная история входов требует дополнительной реализации'
        }
    
    def validate_user_credentials(self, email: str, password: str) -> Tuple[bool, Optional[User], str]:
        """Валидация учетных данных пользователя"""
        try:
            user = User.objects.get(email=email)
            
            if not user.is_active:
                return False, None, 'Аккаунт деактивирован'
            
            if not user.check_password(password):
                return False, None, 'Неверный пароль'
            
            return True, user, 'Успешная аутентификация'
            
        except User.DoesNotExist:
            return False, None, 'Пользователь не найден'
        except Exception as e:
            logger.error(f"Ошибка при валидации учетных данных: {e}")
            return False, None, 'Ошибка сервера'
    
    def exists_by_email(self, email: str) -> bool:
        """Проверка существования пользователя по email"""
        return User.objects.filter(email=email, is_active=True).exists()
    
    def get_optimized_user_queryset(self) -> models.QuerySet[User]:
        """Получение оптимизированного QuerySet для пользователей"""
        return User.objects.filter(is_active=True).select_related()