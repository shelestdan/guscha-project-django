import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes

from .models import CartItem
from .serializers import CartItemSerializer
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
        logger.info(f"Cart list view called for user: {request.user}")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        logger.info(f"Cart data for user {request.user}: {response_data}")
        
        # Создаем кастомный ответ, чтобы он соответствовал ожиданиям фронтенда
        cart_total = sum(item.get('total_price', 0) for item in response_data)
        cart_count = sum(item.get('quantity', 0) for item in response_data)

        custom_response = {
            'items': response_data,
            'count': cart_count,
            'total': cart_total
        }
        
        logger.info(f"Custom response for user {request.user}: {custom_response}")
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
# @permission_classes([IsAuthenticated])
def add_to_cart(request):
    """Добавить товар в корзину"""
    logger.info(f"Add to cart called with data: {request.data}")
    
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

    # Учитываем максимальное количество для заказа
    if size and size.max_quantity is not None:
        if quantity > size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для заказа: {size.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    if cart_item:
        new_quantity = cart_item.quantity + quantity
        if size and size.max_quantity is not None and new_quantity > size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для данного размера: {size.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Если товар уже в корзине, увеличиваем количество
        cart_item.quantity = new_quantity
        cart_item.save()
    else:
        # Создаем новый элемент корзины
        cart_item = CartItem.objects.create(
            **user_kwarg,
            product=product,
            quantity=quantity,
            product_size=size,
            price=product.price,
            item_type='product'
        )
    
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
# @permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """Обновить количество товара в корзине"""
    logger.info(f"Update cart item {item_id} with data: {request.data}")
    
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
    
    # Проверяем максимальное количество для размера товара
    if cart_item.product_size and cart_item.product_size.max_quantity is not None:
        if quantity > cart_item.product_size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для данного размера: {cart_item.product_size.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Проверяем максимальное количество для размера предзаказа
    if cart_item.preorder_size and cart_item.preorder_size.max_quantity is not None:
        if quantity > cart_item.preorder_size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для данного размера: {cart_item.preorder_size.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    cart_item.quantity = quantity
    cart_item.save()
    
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data)


@api_view(['DELETE'])
# @permission_classes([IsAuthenticated])
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
    
    cart_item.delete()
    return Response(
        {"message": "Item removed from cart"}, 
        status=status.HTTP_204_NO_CONTENT
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_preorder_to_cart(request):
    """Добавить предзаказ в корзину"""
    logger.info(f"Add preorder to cart called with data: {request.data}")
    
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
    
    # Проверяем количество на складе
    if size and quantity > size.stock_quantity:
        return Response(
            {"error": f"Недостаточно товара на складе. Доступно: {size.stock_quantity} шт."},
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
        
        # Проверяем количество на складе
        if size and new_quantity > size.stock_quantity:
            return Response(
                {"error": f"Недостаточно товара на складе. Доступно: {size.stock_quantity} шт., в корзине уже {cart_item.quantity} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем максимальное количество для заказа
        if size and size.max_quantity is not None and new_quantity > size.max_quantity:
            return Response(
                {"error": f"Максимальное количество для данного размера: {size.max_quantity}. В корзине уже {cart_item.quantity} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Если предзаказ уже в корзине, увеличиваем количество
        cart_item.quantity = new_quantity
        cart_item.save()
    else:
        # Создаем новый элемент корзины
        cart_item = CartItem.objects.create(
            user=request.user,
            preorder=preorder,
            quantity=quantity,
            preorder_size=size,
            price=preorder.price,
            item_type='preorder'
        )
    
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def clear_cart(request):
    """Очистить корзину пользователя"""
    logger.info(f"Clear cart called")
    
    if request.user.is_authenticated:
        deleted_count, _ = CartItem.objects.filter(user=request.user).delete()
    else:
        session_id = request.headers.get('X-Session-ID')
        if not session_id:
            return Response(
                {"error": "Session ID is required for anonymous users"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        deleted_count, _ = CartItem.objects.filter(session_id=session_id).delete()
    
    return Response(
        {"message": f"Корзина очищена. Удалено товаров: {deleted_count}"}, 
        status=status.HTTP_200_OK
    )
