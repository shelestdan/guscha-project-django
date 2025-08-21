import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt

from .models import CartItem
from .serializers import CartItemSerializer
from .services import ReservationService
from apps.products.models import Product, ProductSize, Preorder, PreorderSize

logger = logging.getLogger(__name__)

class CartViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с корзиной пользователя"""
    serializer_class = CartItemSerializer
    permission_classes = []

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return CartItem.objects.filter(user=self.request.user)
        else:
            session_id = self.request.headers.get('X-Session-ID')
            if session_id:
                return CartItem.objects.filter(session_id=session_id)
            return CartItem.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        
        # Создаем кастомный ответ, чтобы он соответствовал ожиданиям фронтенда
        cart_total = sum(item.get('total_price', 0) for item in response_data)
        cart_count = sum(item.get('quantity', 0) for item in response_data)

        custom_response = {
            'items': response_data,
            'count': cart_count,
            'total': cart_total
        }
        
        return Response(custom_response)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Очистить корзину пользователя"""
        if request.user.is_authenticated:
            CartItem.objects.filter(user=request.user).delete()
        else:
            session_id = request.headers.get('X-Session-ID')
            if session_id:
                CartItem.objects.filter(session_id=session_id).delete()
            else:
                return Response(
                    {"error": "Session ID is required for anonymous users"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response({"message": "Корзина очищена"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@csrf_exempt
@permission_classes([])
def add_to_cart(request):
    """Добавить товар в корзину"""
    logger.info("Add to cart called")
    
    product_id = request.data.get('product')
    quantity = request.data.get('quantity', 1)
    size_id = request.data.get('size')
    
    if not product_id:
        return Response(
            {"error": "Product ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Проверяем размер, если он указан
    size = None
    if size_id:
        try:
            size = ProductSize.objects.get(id=size_id, product=product)
        except ProductSize.DoesNotExist:
            return Response(
                {"error": "Size not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Определяем пользователя или сессию
    if request.user.is_authenticated:
        cart_filter = {'user': request.user}
        user_kwarg = {'user': request.user}
    else:
        session_id = request.headers.get('X-Session-ID')
        if not session_id:
            return Response(
                {"error": "Session ID is required for anonymous users"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_filter = {'session_id': session_id}
        user_kwarg = {'session_id': session_id}
    
    # Проверяем, есть ли уже этот товар в корзине
    cart_item = CartItem.objects.filter(
        **cart_filter,
        product=product,
        product_size=size
    ).first()

    # Проверяем доступность товара с учетом резервирований
    available_quantity = ReservationService.get_available_quantity(
        product=product, product_size=size
    )
    
    if quantity > available_quantity:
        return Response(
            {"error": f"Недостаточно товара на складе. Доступно: {available_quantity} шт."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем максимальное количество для заказа
    if size and size.max_quantity is not None:
        if quantity > size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для заказа: {size.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Проверяем лимит для корзины
    if size and size.limit is not None:
        if quantity > size.limit:
            return Response(
                {"error": f"Максимальное количество для корзины: {size.limit}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    if cart_item:
        new_quantity = cart_item.quantity + quantity
        
        # Проверяем доступность с учетом уже добавленного количества
        # Получаем доступное количество плюс то, что уже в корзине у этого пользователя
        current_available = ReservationService.get_available_quantity(
            product=product, product_size=size
        ) + cart_item.quantity
        
        if new_quantity > current_available:
            return Response(
                {"error": f"Недостаточно товара на складе. Доступно: {current_available} шт., в корзине уже {cart_item.quantity} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем максимальное количество для заказа
        if size and size.max_quantity is not None and new_quantity > size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для данного размера: {size.max_quantity}. В корзине уже {cart_item.quantity} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем лимит для корзины
        if size and size.limit is not None and new_quantity > size.limit:
            return Response(
                {"error": f"Максимальное количество для корзины: {size.limit}. В корзине уже {cart_item.quantity} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Если товар уже в корзине, обновляем количество
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Обновляем резервирование, если оно существует
        if cart_item.reservation:
            success = ReservationService.update_reservation_quantity(
                cart_item.reservation.id, new_quantity
            )
            if not success:
                logger.warning(f"Failed to update reservation for cart item {cart_item.id}")
        # Если резервирования нет, оно будет создано при оформлении заказа
    else:
        # Создаем новый элемент корзины без резервирования
        # Резервирование будет создано только при оформлении заказа
        cart_item = CartItem.objects.create(
            **user_kwarg,
            product=product,
            quantity=quantity,
            product_size=size,
            price=product.price.amount,
            item_type='product'
        )
    
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([])
def create_cart_reservations(request):
    """Создать резервирования для всех товаров в корзине"""
    logger.info("Create cart reservations called")
    
    # Определяем пользователя или сессию
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
        user_kwarg = {'user': request.user}
        session_kwarg = {}
    else:
        session_id = request.headers.get('X-Session-ID')
        if not session_id:
            return Response(
                {"error": "Session ID is required for anonymous users"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_items = CartItem.objects.filter(session_id=session_id)
        user_kwarg = {}
        session_kwarg = {'session_id': session_id}
    
    if not cart_items.exists():
        return Response(
            {"error": "Корзина пуста"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Создаем резервирования для всех товаров в корзине
    reservations_created = []
    errors = []
    
    for cart_item in cart_items:
        try:
            # Проверяем, есть ли уже резервирование для этого элемента корзины
            if cart_item.reservation:
                # Проверяем, не истекло ли резервирование
                if cart_item.reservation.is_expired:
                    logger.info(f"Reservation {cart_item.reservation.id} for cart item {cart_item.id} is expired, removing link")
                    cart_item.reservation = None
                    cart_item.save()
                else:
                    # Обновляем количество в существующем резервировании, если оно отличается
                    if cart_item.reservation.quantity != cart_item.quantity:
                        logger.info(f"Updating reservation {cart_item.reservation.id} quantity from {cart_item.reservation.quantity} to {cart_item.quantity}")
                        success = ReservationService.update_reservation_quantity(
                            cart_item.reservation.id, cart_item.quantity
                        )
                        if success:
                            reservations_created.append({
                                'cart_item_id': cart_item.id,
                                'reservation_id': cart_item.reservation.id,
                                'product_name': cart_item.product.name if cart_item.product else cart_item.preorder.name,
                                'quantity': cart_item.quantity,
                                'status': 'updated'
                            })
                        else:
                            errors.append({
                                'cart_item_id': cart_item.id,
                                'error': 'Не удалось обновить резервирование'
                            })
                    else:
                        logger.info(f"Cart item {cart_item.id} already has valid reservation {cart_item.reservation.id}")
                        reservations_created.append({
                            'cart_item_id': cart_item.id,
                            'reservation_id': cart_item.reservation.id,
                            'product_name': cart_item.product.name if cart_item.product else cart_item.preorder.name,
                            'quantity': cart_item.quantity,
                            'status': 'already_exists'
                        })
                    continue
            
            if cart_item.item_type == 'product':
                reservation = ReservationService.create_reservation(
                    **user_kwarg,
                    **session_kwarg,
                    product=cart_item.product,
                    product_size=cart_item.product_size,
                    quantity=cart_item.quantity
                )
            elif cart_item.item_type == 'preorder':
                reservation = ReservationService.create_reservation(
                    **user_kwarg,
                    **session_kwarg,
                    preorder=cart_item.preorder,
                    preorder_size=cart_item.preorder_size,
                    quantity=cart_item.quantity
                )
            else:
                continue
                
            if reservation:
                # Связываем резервирование с элементом корзины
                cart_item.reservation = reservation
                cart_item.save()
                reservations_created.append({
                    'cart_item_id': cart_item.id,
                    'reservation_id': reservation.id,
                    'product_name': cart_item.product.name if cart_item.product else cart_item.preorder.name,
                    'quantity': cart_item.quantity,
                    'status': 'created'
                })
            else:
                errors.append({
                    'cart_item_id': cart_item.id,
                    'error': 'Не удалось создать резервирование'
                })
                
        except Exception as e:
            logger.error(f"Error creating reservation for cart item {cart_item.id}: {e}")
            errors.append({
                'cart_item_id': cart_item.id,
                'error': str(e)
            })
    
    response_data = {
        'reservations_created': reservations_created,
        'errors': errors,
        'total_reservations': len(reservations_created)
    }
    
    if errors:
        logger.warning(f"Some reservations failed: {errors}")
        return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
    else:
        logger.info(f"All reservations created successfully: {len(reservations_created)}")
        return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([])
def update_cart_item(request, item_id):
    """Обновить количество товара в корзине"""
    logger.info(f"Update cart item {item_id}")
    
    # Определяем пользователя или сессию
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
        else:
            session_id = request.headers.get('X-Session-ID')
            if not session_id:
                return Response(
                    {"error": "Session ID is required for anonymous users"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item = CartItem.objects.get(id=item_id, session_id=session_id)
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    quantity = request.data.get('quantity')
    if quantity is None or quantity < 1:
        return Response(
            {"error": "Valid quantity is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем доступность товара с учетом резервирований
    if cart_item.product:
        # Получаем доступное количество плюс то, что уже зарезервировано для этого элемента корзины
        current_available = ReservationService.get_available_quantity(
            product=cart_item.product, product_size=cart_item.product_size
        ) + cart_item.quantity
        
        if quantity > current_available:
            return Response(
                {"error": f"Недостаточно товара на складе. Доступно: {current_available} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Проверяем максимальное количество для размера товара
    if cart_item.product_size and cart_item.product_size.max_quantity is not None:
        if quantity > cart_item.product_size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для данного размера: {cart_item.product_size.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Проверяем лимит для корзины для товара
    if cart_item.product_size and cart_item.product_size.limit is not None:
        if quantity > cart_item.product_size.limit:
            return Response(
                {"error": f"Максимальное количество для корзины: {cart_item.product_size.limit}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Проверяем доступность предзаказа с учетом резервирований
    if cart_item.preorder:
        current_available = ReservationService.get_available_quantity(
            preorder=cart_item.preorder, preorder_size=cart_item.preorder_size
        ) + cart_item.quantity
        
        if quantity > current_available:
            return Response(
                {"error": f"Недостаточно товара на складе. Доступно: {current_available} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Проверяем максимальное количество для размера предзаказа
    if cart_item.preorder_size and cart_item.preorder_size.max_quantity is not None:
        if quantity > cart_item.preorder_size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для данного размера: {cart_item.preorder_size.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Обновляем резервирование при изменении количества
    if cart_item.reservation:
        # Обновляем количество в резервировании
        success = ReservationService.update_reservation_quantity(
            cart_item.reservation.id, quantity
        )
        if not success:
            return Response(
                {"error": "Не удалось обновить резервирование товара"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    cart_item.quantity = quantity
    cart_item.save()
    
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([])
def remove_cart_item(request, item_id):
    """Удалить товар из корзины"""
    logger.info(f"Remove cart item {item_id}")
    
    # Определяем пользователя или сессию
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
        else:
            session_id = request.headers.get('X-Session-ID')
            if not session_id:
                return Response(
                    {"error": "Session ID is required for anonymous users"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item = CartItem.objects.get(id=item_id, session_id=session_id)
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Отменяем резервирование, если оно существует
    if cart_item.reservation:
        success = ReservationService.cancel_reservation(cart_item.reservation.id)
        if success:
            logger.info(f"Резервирование {cart_item.reservation.id} отменено при удалении товара из корзины")
        else:
            logger.warning(f"Не удалось отменить резервирование {cart_item.reservation.id}")
    
    # Удаляем товар из корзины
    cart_item.delete()
    return Response(
        {"message": "Item removed from cart"}, 
        status=status.HTTP_204_NO_CONTENT
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_preorder_to_cart(request):
    """Добавить предзаказ в корзину"""
    logger.info("Add preorder to cart called")
    
    preorder_id = request.data.get('preorder')
    quantity = request.data.get('quantity', 1)
    size_id = request.data.get('size')
    
    if not preorder_id:
        return Response(
            {"error": "Preorder ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        preorder = Preorder.objects.get(id=preorder_id)
    except Preorder.DoesNotExist:
        return Response(
            {"error": "Preorder not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Проверяем, что предзаказ активен
    if not preorder.is_active_now:
        return Response(
            {"error": "Предзаказ не активен"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем размер, если он указан
    size = None
    if size_id:
        try:
            size = PreorderSize.objects.get(id=size_id, preorder=preorder)
        except PreorderSize.DoesNotExist:
            return Response(
                {"error": "Size not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверяем доступность размера
        if not size.is_available:
            return Response(
                {"error": "Размер недоступен"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Проверяем доступность предзаказа с учетом резервирований
    available_quantity = ReservationService.get_available_quantity(
        preorder=preorder, preorder_size=size
    )
    
    if quantity > available_quantity:
        return Response(
            {"error": f"Недостаточно товара на складе. Доступно: {available_quantity} шт."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем максимальное количество для заказа
    if size and size.max_quantity is not None:
        if quantity > size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для заказа: {size.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Проверяем, есть ли уже этот предзаказ в корзине
    cart_item = CartItem.objects.filter(
        user=request.user,
        preorder=preorder,
        preorder_size=size
    ).first()
    
    if cart_item:
        new_quantity = cart_item.quantity + quantity
        
        # Проверяем доступность с учетом уже добавленного количества
        current_available = ReservationService.get_available_quantity(
            preorder=preorder, preorder_size=size
        ) + cart_item.quantity
        
        if new_quantity > current_available:
            return Response(
                {"error": f"Недостаточно товара на складе. Доступно: {current_available} шт., в корзине уже {cart_item.quantity} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем максимальное количество для заказа
        if size and size.max_quantity is not None and new_quantity > size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для данного размера: {size.max_quantity}. В корзине уже {cart_item.quantity} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Если предзаказ уже в корзине, обновляем количество
        # Резервирование будет создано только при оформлении заказа
        cart_item.quantity = new_quantity
        cart_item.save()
    else:
        # Создаем новый элемент корзины без резервирования
        # Резервирование будет создано только при оформлении заказа
        cart_item = CartItem.objects.create(
            user=request.user,
            preorder=preorder,
            quantity=quantity,
            preorder_size=size,
            price=preorder.price.amount,
            item_type='preorder'
        )
    
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([])
def clear_cart(request):
    """Очистить корзину пользователя"""
    logger.info(f"Clear cart called")
    
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        session_id = request.headers.get('X-Session-ID')
        if not session_id:
            return Response(
                {"error": "Session ID is required for anonymous users"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_items = CartItem.objects.filter(session_id=session_id)
    
    # Отменяем все резервирования перед удалением товаров из корзины
    cancelled_reservations = 0
    for cart_item in cart_items:
        if cart_item.reservation:
            success = ReservationService.cancel_reservation(cart_item.reservation.id)
            if success:
                cancelled_reservations += 1
                logger.info(f"Резервирование {cart_item.reservation.id} отменено при очистке корзины")
            else:
                logger.warning(f"Не удалось отменить резервирование {cart_item.reservation.id}")
    
    # Удаляем товары из корзины
    deleted_count, _ = cart_items.delete()
    
    return Response(
        {"message": f"Корзина очищена. Удалено товаров: {deleted_count}"}, 
        status=status.HTTP_200_OK
    )
