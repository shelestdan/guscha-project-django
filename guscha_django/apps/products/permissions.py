from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение, которое позволяет только администраторам выполнять небезопасные действия"""
    
    def has_permission(self, request, view):
        # Разрешаем GET, HEAD, OPTIONS запросы всем пользователям
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Разрешаем POST, PUT, DELETE только администраторам
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешение, которое позволяет только владельцам объекта редактировать его"""
    
    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD, OPTIONS запросы всем пользователям
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Разрешаем редактирование только владельцу объекта
        return obj.user == request.user