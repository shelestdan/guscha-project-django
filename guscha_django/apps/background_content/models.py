from django.db import models
from django.core.validators import URLValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
import re
from PIL import Image
import os
from .validators import background_image_validator


def background_image_upload_path(instance, filename):
    """Генерация пути для загрузки фоновых изображений"""
    import uuid
    from pathlib import Path
    
    # Получаем расширение файла
    ext = Path(filename).suffix.lower()
    # Генерируем уникальное имя файла
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    return f"backgrounds/{unique_filename}"


def slideshow_image_upload_path(instance, filename):
    """Генерация пути для загрузки изображений слайдшоу"""
    import uuid
    from pathlib import Path
    
    # Получаем расширение файла
    ext = Path(filename).suffix.lower()
    # Генерируем уникальное имя файла
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    return f"slideshow/{unique_filename}"


class BackgroundContent(models.Model):
    """Базовая модель для управления фоновым контентом главной страницы"""
    CONTENT_TYPES = [
        ('image', 'Изображение'),
        ('slideshow', 'Слайдшоу'),
        ('video', 'Видео'),
    ]
    
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        verbose_name='Тип контента'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='Активен'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Фоновый контент'
        verbose_name_plural = 'Фоновый контент'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"
    
    def save(self, *args, **kwargs):
        # Деактивировать другой активный контент при активации нового
        if self.is_active:
            BackgroundContent.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class BackgroundImage(models.Model):
    """Модель для одиночных фоновых изображений"""
    SCALING_MODES = [
        ('cover', 'Покрыть (cover)'),
        ('contain', 'Вместить (contain)'),
        ('fill', 'Заполнить (fill)'),
    ]
    
    background_content = models.OneToOneField(
        BackgroundContent,
        on_delete=models.CASCADE,
        related_name='background_image',
        verbose_name='Фоновый контент'
    )
    image = models.ImageField(
        upload_to=background_image_upload_path,
        verbose_name='Изображение',
        validators=[
            background_image_validator.validate_image_file,
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
                message='Поддерживаемые форматы: JPG, JPEG, PNG, WebP'
            )
        ],
        help_text='Поддерживаемые форматы: JPG, JPEG, PNG, WebP. Максимальный размер: 15MB. Минимальный размер: 400x300px.'
    )
    width = models.PositiveIntegerField(
        default=1920,
        verbose_name='Ширина'
    )
    height = models.PositiveIntegerField(
        default=1080,
        verbose_name='Высота'
    )
    scaling_mode = models.CharField(
        max_length=20,
        choices=SCALING_MODES,
        default='cover',
        verbose_name='Режим масштабирования'
    )
    is_primary = models.BooleanField(
        default=True,
        verbose_name='Основное изображение',
        help_text='Использовать это изображение как основное для фона сайта'
    )
    
    class Meta:
        verbose_name = 'Фоновое изображение'
        verbose_name_plural = 'Фоновые изображения'
    
    def save(self, *args, **kwargs):
        # Автоматическое определение размеров изображения
        if self.image and hasattr(self.image, 'file'):
            try:
                with Image.open(self.image.file) as img:
                    self.width, self.height = img.size
            except Exception as e:
                # Логируем ошибку, но не прерываем сохранение
                print(f"Ошибка при определении размеров изображения: {e}")
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Изображение для {self.background_content.title}"


class Slideshow(models.Model):
    """Модель для настроек слайдшоу"""
    background_content = models.OneToOneField(
        BackgroundContent,
        on_delete=models.CASCADE,
        related_name='slideshow',
        verbose_name='Фоновый контент'
    )
    interval = models.PositiveIntegerField(
        default=5000,
        verbose_name='Интервал смены (мс)',
        help_text='Интервал между слайдами в миллисекундах'
    )
    transition_duration = models.PositiveIntegerField(
        default=1000,
        verbose_name='Длительность перехода (мс)',
        help_text='Длительность анимации перехода в миллисекундах'
    )
    
    class Meta:
        verbose_name = 'Слайдшоу'
        verbose_name_plural = 'Слайдшоу'
    
    def __str__(self):
        return f"Слайдшоу для {self.background_content.title}"


class SlideshowImage(models.Model):
    """Модель для изображений в слайдшоу"""
    slideshow = models.ForeignKey(
        Slideshow,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Слайдшоу'
    )
    image = models.ImageField(
        upload_to=slideshow_image_upload_path,
        verbose_name='Изображение',
        validators=[
            background_image_validator.validate_slideshow_image,
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
                message='Поддерживаемые форматы: JPG, JPEG, PNG, WebP'
            )
        ],
        help_text='Поддерживаемые форматы: JPG, JPEG, PNG, WebP. Максимальный размер: 15MB. Минимальный размер: 400x300px. Рекомендуемое соотношение сторон: 16:9.'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок отображения'
    )
    is_primary = models.BooleanField(default=False, verbose_name='Основное изображение')
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ширина')
    height = models.PositiveIntegerField(null=True, blank=True, verbose_name='Высота')
    
    class Meta:
        verbose_name = 'Изображение слайдшоу'
        verbose_name_plural = 'Изображения слайдшоу'
        ordering = ['order']
    
    def save(self, *args, **kwargs):
        # Автоматическое определение размеров изображения
        if self.image and hasattr(self.image, 'file'):
            try:
                with Image.open(self.image.file) as img:
                    self.width, self.height = img.size
            except Exception as e:
                # Логируем ошибку, но не прерываем сохранение
                print(f"Ошибка при определении размеров изображения: {e}")
        
        # Если это основное изображение, убираем флаг у других изображений этого слайдшоу
        if self.is_primary:
            SlideshowImage.objects.filter(
                slideshow=self.slideshow,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        primary_text = " (Основное)" if self.is_primary else ""
        return f"Слайд {self.order} для {self.slideshow.background_content.title}{primary_text}"


class BackgroundVideo(models.Model):
    """Модель для фоновых видео с поддержкой YouTube и Vimeo"""
    PLATFORMS = [
        ('youtube', 'YouTube'),
        ('vimeo', 'Vimeo'),
    ]
    
    background_content = models.OneToOneField(
        BackgroundContent,
        on_delete=models.CASCADE,
        related_name='background_video',
        verbose_name='Фоновый контент'
    )
    video_url = models.URLField(
        max_length=500,
        verbose_name='URL видео',
        help_text='Ссылка на YouTube или Vimeo видео'
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORMS,
        default='youtube',
        verbose_name='Платформа'
    )
    autoplay = models.BooleanField(
        default=True,
        verbose_name='Автовоспроизведение'
    )
    muted = models.BooleanField(
        default=True,
        verbose_name='Без звука'
    )
    loop = models.BooleanField(
        default=True,
        verbose_name='Зацикливание'
    )
    
    # Настройки плейлиста
    playlist_order = models.PositiveIntegerField(default=0, verbose_name="Порядок в плейлисте")
    playlist_mode = models.BooleanField(default=False, verbose_name="Режим плейлиста")
    
    class Meta:
        verbose_name = 'Фоновое видео'
        verbose_name_plural = 'Фоновые видео'
    
    def __str__(self):
        return f"Видео для {self.background_content.title}"
    
    def clean(self):
        """Валидация URL видео для поддерживаемых платформ"""
        super().clean()
        
        youtube_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w\-_]+)'
        vimeo_pattern = r'(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(\d+)'
        
        if self.platform == 'youtube':
            if not re.match(youtube_pattern, self.video_url):
                raise ValidationError('Неверный формат URL для YouTube видео')
        elif self.platform == 'vimeo':
            if not re.match(vimeo_pattern, self.video_url):
                raise ValidationError('Неверный формат URL для Vimeo видео')
    
    def get_embed_url(self):
        """Получение URL для встраивания видео"""
        if self.platform == 'youtube':
            youtube_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w\-_]+)'
            match = re.match(youtube_pattern, self.video_url)
            if match:
                video_id = match.group(1)
                params = []
                if self.autoplay:
                    params.append('autoplay=1')
                if self.muted:
                    params.append('mute=1')
                if self.loop:
                    params.append(f'loop=1&playlist={video_id}')
                params.append('controls=0')
                params.append('showinfo=0')
                params.append('rel=0')
                param_string = '&'.join(params)
                return f'https://www.youtube.com/embed/{video_id}?{param_string}'
        
        elif self.platform == 'vimeo':
            vimeo_pattern = r'(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(\d+)'
            match = re.match(vimeo_pattern, self.video_url)
            if match:
                video_id = match.group(1)
                params = []
                if self.autoplay:
                    params.append('autoplay=1')
                if self.muted:
                    params.append('muted=1')
                if self.loop:
                    params.append('loop=1')
                params.append('background=1')
                param_string = '&'.join(params)
                return f'https://player.vimeo.com/video/{video_id}?{param_string}'
        
        return self.video_url
