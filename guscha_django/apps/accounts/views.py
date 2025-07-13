from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model, logout
from django.utils.translation import gettext_lazy as _

from .serializers import (
    UserSerializer, 
    UserCreateSerializer, 
    UserUpdateSerializer, 
    ChangePasswordSerializer,
    LoginSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return self.serializer_class
    
    def get_permissions(self):
        """Настройка прав доступа в зависимости от действия"""
        if self.action == 'create' or self.action == 'login' or self.action == 'google_login':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        """Создание нового пользователя"""
        print(f"DEBUG: Received data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        print(f"DEBUG: Using serializer: {type(serializer).__name__}")
        
        if not serializer.is_valid():
            print(f"DEBUG: Validation errors: {serializer.errors}")
            
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Создаем токен для нового пользователя
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Аутентификация пользователя"""
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Получаем или создаем токен для пользователя
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Выход пользователя из системы"""
        # Удаляем токен пользователя
        Token.objects.filter(user=request.user).delete()
        
        # Выполняем стандартный выход
        logout(request)
        
        return Response({"detail": _('Успешный выход из системы.')}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Получение и обновление информации о текущем пользователе"""
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = UserUpdateSerializer(
                request.user, 
                data=request.data, 
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # Возвращаем обновленные данные пользователя
            return Response(UserSerializer(request.user).data)
    
    @action(detail=False, methods=['put'])
    def change_password(self, request):
        """Изменение пароля пользователя"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Проверяем старый пароль
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"old_password": _('Неверный пароль')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Устанавливаем новый пароль
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        # Обновляем токен пользователя
        Token.objects.filter(user=request.user).delete()
        token, created = Token.objects.get_or_create(user=request.user)
        
        return Response({
            "detail": _('Пароль успешно изменен.'),
            "token": token.key
        }, status=status.HTTP_200_OK)
