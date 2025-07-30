from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import CartItem, Reservation
from apps.products.models import Product, ProductSize, Preorder, PreorderSize
import logging

logger = logging.getLogger(__name__)


class ReservationService:
    """Сервис для управления резервированиями товаров"""
    
    DEFAULT_RESERVATION_TIME = 30  # минут
    
    @classmethod
    def create_reservation(cls, user=None, session_id=None, product=None, product_size=None,
                          preorder=None, preorder_size=None, quantity=1, 
                          reservation_minutes=None):
        """
        Создание резервирования товара
        
        Args:
            user: Пользователь (для авторизованных)
            session_id: ID сессии (для анонимных)
            product: Товар
            product_size: Размер товара
            preorder: Предзаказ
            preorder_size: Размер предзаказа
            quantity: Количество для резервирования
            reservation_minutes: Время резервирования в минутах
            
        Returns:
            Reservation: Созданное резервирование или None при ошибке
        """
        if reservation_minutes is None:
            reservation_minutes = cls.DEFAULT_RESERVATION_TIME
            
        expires_at = timezone.now() + timedelta(minutes=reservation_minutes)
        
        try:
            with transaction.atomic():
                # Проверяем доступность товара
                if not cls._check_availability(product, product_size, preorder, 
                                              preorder_size, quantity):
                    logger.warning(f"Недостаточно товара для резервирования: {quantity}")
                    return None
                
                # Создаем резервирование
                reservation = Reservation.objects.create(
                    user=user,
                    session_id=session_id,
                    product=product,
                    product_size=product_size,
                    preorder=preorder,
                    preorder_size=preorder_size,
                    quantity=quantity,
                    expires_at=expires_at
                )
                
                logger.info(f"Создано резервирование {reservation.id} на {quantity} единиц")
                return reservation
                
        except Exception as e:
            logger.error(f"Ошибка при создании резервирования: {e}")
            return None
    
    @classmethod
    def _check_availability(cls, product=None, product_size=None, preorder=None,
                           preorder_size=None, quantity=1):
        """
        Проверка доступности товара с учетом активных резервирований
        
        Returns:
            bool: True если товар доступен в нужном количестве
        """
        # Получаем общее количество на складе
        if product_size:
            total_stock = product_size.stock_quantity
            # Получаем активные резервирования для этого размера
            reserved_quantity = cls._get_reserved_quantity(
                product=product, product_size=product_size
            )
            item_info = f"товар {product.name} размер {product_size.size_name}"
        elif preorder_size:
            total_stock = preorder_size.stock_quantity
            # Получаем активные резервирования для этого размера предзаказа
            reserved_quantity = cls._get_reserved_quantity(
                preorder=preorder, preorder_size=preorder_size
            )
            item_info = f"предзаказ {preorder.name} размер {preorder_size.size_name}"
        elif product:
            total_stock = product.stock_quantity
            # Получаем активные резервирования для товара
            reserved_quantity = cls._get_reserved_quantity(product=product)
            item_info = f"товар {product.name}"
        else:
            logger.error("Не указан товар или предзаказ для проверки доступности")
            return False
        
        available_quantity = total_stock - reserved_quantity
        is_available = available_quantity >= quantity
        
        logger.info(f"Проверка доступности для {item_info}: "
                   f"на складе={total_stock}, зарезервировано={reserved_quantity}, "
                   f"доступно={available_quantity}, запрошено={quantity}, "
                   f"результат={'доступно' if is_available else 'недоступно'}")
        
        return is_available
    
    @classmethod
    def _get_reserved_quantity(cls, product=None, product_size=None, 
                              preorder=None, preorder_size=None):
        """
        Получение количества зарезервированного товара
        
        Returns:
            int: Общее количество зарезервированного товара
        """
        # Очищаем истекшие резервирования
        cls.cleanup_expired_reservations()
        
        filters = {'status': 'active'}
        
        if product_size:
            filters.update({
                'product': product,
                'product_size': product_size
            })
        elif preorder_size:
            filters.update({
                'preorder': preorder,
                'preorder_size': preorder_size
            })
        elif product:
            filters['product'] = product
        elif preorder:
            filters['preorder'] = preorder
        else:
            return 0
        
        reservations = Reservation.objects.filter(**filters)
        return sum(r.quantity for r in reservations)
    
    @classmethod
    def get_available_quantity(cls, product=None, product_size=None,
                              preorder=None, preorder_size=None):
        """
        Получение доступного количества товара с учетом резервирований
        
        Returns:
            int: Доступное количество товара
        """
        if product_size:
            total_stock = product_size.stock_quantity
            reserved_quantity = cls._get_reserved_quantity(
                product=product, product_size=product_size
            )
        elif preorder_size:
            total_stock = preorder_size.stock_quantity
            reserved_quantity = cls._get_reserved_quantity(
                preorder=preorder, preorder_size=preorder_size
            )
        elif product:
            total_stock = product.stock_quantity
            reserved_quantity = cls._get_reserved_quantity(product=product)
        else:
            return 0
        
        return max(0, total_stock - reserved_quantity)
    
    @classmethod
    def extend_reservation(cls, reservation_id, minutes=30):
        """
        Продление резервирования
        
        Args:
            reservation_id: ID резервирования
            minutes: Количество минут для продления
            
        Returns:
            bool: True если продление успешно
        """
        try:
            reservation = Reservation.objects.get(id=reservation_id, status='active')
            reservation.extend_reservation(minutes)
            logger.info(f"Резервирование {reservation_id} продлено на {minutes} минут")
            return True
        except Reservation.DoesNotExist:
            logger.warning(f"Резервирование {reservation_id} не найдено")
            return False
        except Exception as e:
            logger.error(f"Ошибка при продлении резервирования {reservation_id}: {e}")
            return False
    
    @classmethod
    def update_reservation_quantity(cls, reservation_id, new_quantity, minutes=30):
        """
        Обновление количества в резервировании с проверкой доступности
        
        Args:
            reservation_id: ID резервирования
            new_quantity: Новое количество
            minutes: Количество минут для продления
            
        Returns:
            bool: True если обновление успешно
        """
        try:
            with transaction.atomic():
                reservation = Reservation.objects.get(id=reservation_id, status='active')
                
                # Проверяем доступность с учетом текущего резервирования
                if reservation.product_size:
                    available = cls.get_available_quantity(
                        product=reservation.product, 
                        product_size=reservation.product_size
                    ) + reservation.quantity  # Добавляем текущее количество резервирования
                elif reservation.preorder_size:
                    available = cls.get_available_quantity(
                        preorder=reservation.preorder, 
                        preorder_size=reservation.preorder_size
                    ) + reservation.quantity
                elif reservation.product:
                    available = cls.get_available_quantity(
                        product=reservation.product
                    ) + reservation.quantity
                else:
                    logger.error(f"Резервирование {reservation_id} не имеет связанного товара")
                    return False
                
                if new_quantity > available:
                    logger.warning(f"Недостаточно товара для обновления резервирования {reservation_id}: запрошено {new_quantity}, доступно {available}")
                    return False
                
                # Обновляем количество и продлеваем резервирование
                reservation.quantity = new_quantity
                reservation.extend_reservation(minutes)
                reservation.save()
                
                logger.info(f"Резервирование {reservation_id} обновлено: количество {new_quantity}, продлено на {minutes} минут")
                return True
                
        except Reservation.DoesNotExist:
            logger.warning(f"Резервирование {reservation_id} не найдено")
            return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении резервирования {reservation_id}: {e}")
            return False
    
    @classmethod
    def cancel_reservation(cls, reservation_id):
        """
        Отмена резервирования
        
        Args:
            reservation_id: ID резервирования
            
        Returns:
            bool: True если отмена успешна
        """
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.cancel()
            logger.info(f"Резервирование {reservation_id} отменено")
            return True
        except Reservation.DoesNotExist:
            logger.warning(f"Резервирование {reservation_id} не найдено")
            return False
        except Exception as e:
            logger.error(f"Ошибка при отмене резервирования {reservation_id}: {e}")
            return False
    
    @classmethod
    def complete_reservation(cls, reservation_id):
        """
        Завершение резервирования (при оформлении заказа)
        
        Args:
            reservation_id: ID резервирования
            
        Returns:
            bool: True если завершение успешно
        """
        try:
            reservation = Reservation.objects.get(id=reservation_id, status='active')
            reservation.complete()
            logger.info(f"Резервирование {reservation_id} завершено")
            return True
        except Reservation.DoesNotExist:
            logger.warning(f"Активное резервирование {reservation_id} не найдено")
            return False
        except Exception as e:
            logger.error(f"Ошибка при завершении резервирования {reservation_id}: {e}")
            return False
    
    @classmethod
    def cleanup_expired_reservations(cls):
        """
        Очистка истекших резервирований
        
        Returns:
            int: Количество очищенных резервирований
        """
        try:
            count = Reservation.cleanup_expired()
            if count > 0:
                logger.info(f"Очищено {count} истекших резервирований")
            return count
        except Exception as e:
            logger.error(f"Ошибка при очистке истекших резервирований: {e}")
            return 0
    
    @classmethod
    def get_user_reservations(cls, user=None, session_id=None, active_only=True):
        """
        Получение резервирований пользователя
        
        Args:
            user: Пользователь
            session_id: ID сессии
            active_only: Только активные резервирования
            
        Returns:
            QuerySet: Резервирования пользователя
        """
        filters = {}
        
        if user:
            filters['user'] = user
        elif session_id:
            filters['session_id'] = session_id
        else:
            return Reservation.objects.none()
        
        if active_only:
            filters['status'] = 'active'
            # Также проверяем, что резервирование не истекло
            filters['expires_at__gt'] = timezone.now()
        
        return Reservation.objects.filter(**filters)