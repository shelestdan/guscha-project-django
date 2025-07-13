from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, OrderCreateSerializer
from .filters import OrderFilter


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления заказами
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter
    
    def get_permissions(self):
        """
        Устанавливаем разрешения в зависимости от действия
        """
        if self.action in ['list', 'retrieve', 'create']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Фильтруем заказы в зависимости от пользователя
        """
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """
        Выбираем сериализатор в зависимости от действия
        """
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Отмена заказа
        """
        order = self.get_object()
        
        if order.status not in ['pending', 'confirmed']:
            return Response(
                {'error': 'Заказ нельзя отменить в текущем статусе'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        return Response({'status': 'Заказ отменен'})
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Подтверждение заказа (только для админов)
        """
        order = self.get_object()
        
        if order.status != 'pending':
            return Response(
                {'error': 'Заказ можно подтвердить только в статусе ожидания'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'confirmed'
        order.save()
        
        return Response({'status': 'Заказ подтвержден'})
    
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """
        Отметка заказа как отправленного (только для админов)
        """
        order = self.get_object()
        
        if order.status != 'confirmed':
            return Response(
                {'error': 'Заказ можно отправить только после подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'shipped'
        order.save()
        
        return Response({'status': 'Заказ отправлен'})
    
    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """
        Отметка заказа как доставленного (только для админов)
        """
        order = self.get_object()
        
        if order.status != 'shipped':
            return Response(
                {'error': 'Заказ можно отметить как доставленный только после отправки'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'delivered'
        order.save()
        
        return Response({'status': 'Заказ доставлен'})


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра элементов заказов
    """
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Фильтруем элементы заказов в зависимости от пользователя
        """
        if self.request.user.is_staff:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_order(self, request):
        """
        Получение всех элементов конкретного заказа
        """
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response(
                {'error': 'Необходимо указать order_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = Order.objects.get(id=order_id)
            if not request.user.is_staff and order.user != request.user:
                return Response(
                    {'error': 'У вас нет доступа к этому заказу'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            items = OrderItem.objects.filter(order=order)
            serializer = self.get_serializer(items, many=True)
            return Response(serializer.data)
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Заказ не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
