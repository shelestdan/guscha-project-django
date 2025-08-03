from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.urls import reverse
from apps.products.models import BaseModel
from apps.products.validators import ImageValidator
from apps.products.utils.image_utils import ImageProcessor
import os


def collection_image_upload_path(instance, filename):
    """Генерирует путь для загрузки изображений коллекций"""
    ext = filename.split('.')[-1]
    filename = f"{instance.collection.slug}_{instance.id or 'new'}.{ext}"
    return os.path.join('collections', 'images', filename)


class Collection(BaseModel):
    """Модель коллекции товаров"""
    
    name = models.CharField(
        max_length=200,
        verbose_name="Название коллекции",
        help_text="Название коллекции (максимум 200 символов)"
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="URL-адрес",
        help_text="Уникальный URL-адрес коллекции"
    )
    
    description = models.TextField(
        verbose_name="Описание",
        help_text="Подробное описание коллекции",
        blank=True
    )
    
    short_description = models.CharField(
        max_length=500,
        verbose_name="Краткое описание",
        help_text="Краткое описание для превью (максимум 500 символов)",
        blank=True
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
        help_text="Отображать ли коллекцию на сайте"
    )
    
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки",
        help_text="Порядок отображения коллекций (меньше = выше)"
    )
    
    featured = models.BooleanField(
        default=False,
        verbose_name="Рекомендуемая",
        help_text="Отмечать ли коллекцию как рекомендуемую"
    )
    
    # SEO поля
    meta_title = models.CharField(
        max_length=60,
        verbose_name="Meta Title",
        help_text="SEO заголовок (максимум 60 символов)",
        blank=True
    )
    
    meta_description = models.CharField(
        max_length=160,
        verbose_name="Meta Description",
        help_text="SEO описание (максимум 160 символов)",
        blank=True
    )
    
    class Meta:
        verbose_name = "Коллекция"
        verbose_name_plural = "Коллекции"
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['featured', 'is_active']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Автоматическое создание slug при сохранении"""
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Обеспечиваем уникальность slug
        original_slug = self.slug
        counter = 1
        while Collection.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Возвращает URL коллекции"""
        return f'/api/collections/{self.slug}/'
    
    def get_images(self):
        """Возвращает все изображения коллекции, отсортированные по порядку"""
        return self.images.filter(is_active=True).order_by('sort_order', 'created_at')
    
    def get_primary_image(self):
        """Возвращает основное изображение коллекции"""
        primary = self.images.filter(is_primary=True, is_active=True).first()
        if primary:
            return primary
        return self.images.filter(is_active=True).order_by('sort_order', 'created_at').first()
    
    def get_image_url(self):
        """Возвращает URL основного изображения"""
        primary_image = self.get_primary_image()
        if primary_image:
            return primary_image.get_image_url()
        return None


class CollectionImage(BaseModel):
    """Модель изображений коллекции"""
    
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Коллекция"
    )
    
    image = models.ImageField(
        upload_to=collection_image_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])
        ],
        verbose_name="Изображение",
        help_text="Изображение коллекции (форматы: JPG, PNG, WebP)"
    )
    
    image_url = models.URLField(
        verbose_name="URL изображения",
        help_text="Альтернативный URL изображения (если не загружено локально)",
        blank=True,
        null=True
    )
    
    alt_text = models.CharField(
        max_length=200,
        verbose_name="Alt текст",
        help_text="Альтернативный текст для изображения (для SEO и доступности)",
        blank=True
    )
    
    caption = models.CharField(
        max_length=500,
        verbose_name="Подпись",
        help_text="Подпись к изображению",
        blank=True
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Основное изображение",
        help_text="Использовать как основное изображение коллекции"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно",
        help_text="Отображать ли изображение"
    )
    
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки",
        help_text="Порядок отображения изображений"
    )
    
    # Метаданные изображения
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Ширина",
        help_text="Ширина изображения в пикселях"
    )
    
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Высота",
        help_text="Высота изображения в пикселях"
    )
    
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Размер файла",
        help_text="Размер файла в байтах"
    )
    
    class Meta:
        verbose_name = "Изображение коллекции"
        verbose_name_plural = "Изображения коллекций"
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['collection', 'is_active', 'sort_order']),
            models.Index(fields=['collection', 'is_primary']),
        ]
        constraints = [
            # Только одно основное изображение на коллекцию
            models.UniqueConstraint(
                fields=['collection'],
                condition=models.Q(is_primary=True),
                name='unique_primary_image_per_collection'
            )
        ]
    
    def __str__(self):
        return f"Изображение для {self.collection.name}"
    
    def save(self, *args, **kwargs):
        """Обработка изображения при сохранении"""
        # Если это основное изображение, убираем флаг у других
        if self.is_primary:
            CollectionImage.objects.filter(
                collection=self.collection,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        # Обработка изображения
        if self.image and hasattr(self.image, 'file'):
            processor = ImageProcessor()
            
            # Получаем метаданные
            metadata = processor.get_image_metadata(self.image)
            if metadata:
                self.width = metadata.get('width')
                self.height = metadata.get('height')
                self.file_size = metadata.get('file_size')
            
            # Оптимизируем изображение
            try:
                processor.optimize_image(
                    self.image.path,
                    max_width=1920,
                    max_height=1080,
                    quality=85
                )
            except Exception as e:
                # Логируем ошибку, но не прерываем сохранение
                print(f"Ошибка оптимизации изображения: {e}")
        
        super().save(*args, **kwargs)
    
    def get_image_url(self):
        """Возвращает URL изображения"""
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        return None
    
    def get_thumbnail_url(self, width=300, height=300):
        """Возвращает URL миниатюры изображения"""
        # Здесь можно добавить логику создания миниатюр
        # Пока возвращаем оригинальное изображение
        return self.get_image_url()