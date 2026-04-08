# -*- coding: utf-8 -*-
"""
Сериализаторы для коллекций.

Этот модуль содержит сериализаторы для API коллекций товаров.
"""

from rest_framework import serializers
from .models import Collection, CollectionImage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CollectionImageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для изображений коллекций.
    """
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CollectionImage
        fields = [
            'id',
            'image',
            'image_url',
            'thumbnail_url',
            'alt_text',
            'caption',
            'sort_order',
            'is_active',
            'is_primary',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """
        Получение полного URL изображения.
        """
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_thumbnail_url(self, obj):
        """
        Получение URL миниатюры изображения.
        """
        # Здесь можно добавить логику для создания миниатюр
        # Пока возвращаем основное изображение
        return self.get_image_url(obj)


class CollectionListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка коллекций (краткая информация).
    """
    main_image = serializers.SerializerMethodField()
    images_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'slug',
            'short_description',
            'main_image',
            'images_count',
            'is_featured',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_main_image(self, obj):
        """
        Получение главного изображения коллекции.
        """
        main_image = obj.images.filter(is_active=True).order_by('order', 'created_at').first()
        if main_image:
            return CollectionImageSerializer(main_image, context=self.context).data
        return None
    
    def get_images_count(self, obj):
        """
        Получение количества активных изображений в коллекции.
        """
        return obj.images.filter(is_active=True).count()


class CollectionDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детальной информации о коллекции.
    """
    images = CollectionImageSerializer(many=True, read_only=True)
    images_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'short_description',
            'images',
            'images_count',
            'is_featured',
            'is_active',
            'meta_title',
            'meta_description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_images_count(self, obj):
        """
        Получение количества активных изображений в коллекции.
        """
        return obj.images.filter(is_active=True).count()


class CollectionSerializer(serializers.ModelSerializer):
    """
    Основной сериализатор для коллекций.
    Автоматически выбирает уровень детализации в зависимости от контекста.
    """
    images = CollectionImageSerializer(many=True, read_only=True)
    main_image = serializers.SerializerMethodField()
    images_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'short_description',
            'images',
            'main_image',
            'images_count',
            'is_featured',
            'is_active',
            'meta_title',
            'meta_description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        """
        Динамическое исключение полей в зависимости от контекста.
        """
        super().__init__(*args, **kwargs)
        
        # Для списка коллекций исключаем полное описание и все изображения
        request = self.context.get('request')
        if request and hasattr(request, 'resolver_match'):
            view_name = request.resolver_match.view_name
            if 'list' in view_name.lower():
                # Для списка показываем только краткую информацию
                self.fields.pop('description', None)
                self.fields.pop('images', None)
                self.fields.pop('meta_title', None)
                self.fields.pop('meta_description', None)
    
    def get_main_image(self, obj):
        """
        Получение главного изображения коллекции.
        """
        main_image = obj.images.filter(is_active=True).order_by('order', 'created_at').first()
        if main_image:
            return CollectionImageSerializer(main_image, context=self.context).data
        return None
    
    def get_images_count(self, obj):
        """
        Получение количества активных изображений в коллекции.
        """
        return obj.images.filter(is_active=True).count()
    
    def validate_name(self, value):
        """
        Валидация названия коллекции.
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Название коллекции должно содержать минимум 2 символа."
            )
        return value.strip()
    
    def validate_short_description(self, value):
        """
        Валидация краткого описания.
        """
        if value and len(value.strip()) > 200:
            raise serializers.ValidationError(
                "Краткое описание не должно превышать 200 символов."
            )
        return value.strip() if value else value
    
    def validate_description(self, value):
        """
        Валидация полного описания.
        """
        if value and len(value.strip()) > 5000:
            raise serializers.ValidationError(
                "Описание не должно превышать 5000 символов."
            )
        return value.strip() if value else value


class CollectionCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления коллекций.
    """
    
    class Meta:
        model = Collection
        fields = [
            'name',
            'description',
            'short_description',
            'is_featured',
            'is_active',
            'meta_title',
            'meta_description'
        ]
    
    def validate_name(self, value):
        """
        Валидация названия коллекции.
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Название коллекции должно содержать минимум 2 символа."
            )
        
        # Проверка уникальности названия
        instance = getattr(self, 'instance', None)
        if Collection.objects.filter(name__iexact=value.strip()).exclude(
            id=instance.id if instance else None
        ).exists():
            raise serializers.ValidationError(
                "Коллекция с таким названием уже существует."
            )
        
        return value.strip()
    
    def create(self, validated_data):
        """
        Создание новой коллекции.
        """
        try:
            collection = Collection.objects.create(**validated_data)
            logger.info(f'Создана новая коллекция: {collection.name} (ID: {collection.id})')
            return collection
        except Exception as e:
            logger.error(f'Ошибка при создании коллекции: {e}')
            raise serializers.ValidationError(
                "Произошла ошибка при создании коллекции."
            )
    
    def update(self, instance, validated_data):
        """
        Обновление существующей коллекции.
        """
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            logger.info(f'Обновлена коллекция: {instance.name} (ID: {instance.id})')
            return instance
        except Exception as e:
            logger.error(f'Ошибка при обновлении коллекции {instance.id}: {e}')
            raise serializers.ValidationError(
                "Произошла ошибка при обновлении коллекции."
            )