from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Address
from .serializers import (
    AddressSerializer, AddressCreateSerializer, 
    AddressUpdateSerializer, AddressListSerializer
)


class AddressViewSet(viewsets.ModelViewSet):
    """ViewSet для управления адресами пользователя"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Получение адресов текущего пользователя"""
        return Address.objects.filter(user=self.request.user, is_active=True)
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return AddressListSerializer
        elif self.action == 'create':
            return AddressCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AddressUpdateSerializer
        return AddressSerializer
    
    def perform_create(self, serializer):
        """Установка пользователя при создании адреса"""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Создание адреса с возвратом полного объекта включая ID"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Возвращаем полный объект с ID через AddressSerializer
        instance = serializer.instance
        response_serializer = AddressSerializer(instance, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_destroy(self, instance):
        """Мягкое удаление адреса (деактивация)"""
        instance.is_active = False
        instance.save()
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Получение адресов по умолчанию"""
        default_shipping = self.get_queryset().filter(
            address_type='shipping', is_default=True
        ).first()
        
        default_billing = self.get_queryset().filter(
            address_type='billing', is_default=True
        ).first()
        
        return Response({
            'shipping': AddressSerializer(default_shipping).data if default_shipping else None,
            'billing': AddressSerializer(default_billing).data if default_billing else None,
        })
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Установка адреса по умолчанию"""
        address = self.get_object()
        
        # Отключаем другие адреса по умолчанию
        Address.objects.filter(
            user=request.user,
            address_type=address.address_type,
            is_default=True
        ).exclude(id=address.id).update(is_default=False)
        
        # Устанавливаем текущий адрес по умолчанию
        address.is_default = True
        address.save()
        
        return Response({
            'message': 'Адрес установлен по умолчанию',
            'address': AddressSerializer(address).data
        })
    
    @action(detail=False, methods=['get'])
    def shipping(self, request):
        """Получение всех адресов доставки"""
        addresses = self.get_queryset().filter(address_type='shipping')
        serializer = self.get_serializer(addresses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def billing(self, request):
        """Получение всех адресов оплаты"""
        addresses = self.get_queryset().filter(address_type='billing')
        serializer = self.get_serializer(addresses, many=True)
        return Response(serializer.data)