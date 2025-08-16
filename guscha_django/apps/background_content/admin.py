from django.contrib import admin
from django.contrib.admin import StackedInline, ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.widgets import (
    UnfoldAdminImageFieldWidget,
    UnfoldAdminTextInputWidget,
    UnfoldAdminSelectWidget
)
from django import forms
from django.db import models
from django.utils.html import format_html
from PIL import Image
import logging
from .models import (
    BackgroundContent,
    BackgroundImage,
    Slideshow,
    SlideshowImage,
    BackgroundVideo
)


class BackgroundImageForm(forms.ModelForm):
    """Форма для фонового изображения с правильными виджетами"""
    
    class Meta:
        model = BackgroundImage
        fields = ['image', 'scaling_mode']
        widgets = {
            'image': UnfoldAdminImageFieldWidget(attrs={
                'accept': 'image/jpeg,image/png,image/webp'
            }),
            'scaling_mode': UnfoldAdminSelectWidget()
        }


class SlideshowImageForm(forms.ModelForm):
    """Форма для изображений слайдшоу с правильными виджетами"""
    
    class Meta:
        model = SlideshowImage
        fields = ['image', 'order', 'is_primary']
        widgets = {
            'image': UnfoldAdminImageFieldWidget(attrs={
                'accept': 'image/jpeg,image/png,image/webp'
            }),
            'order': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '0'
            })
        }


class EnhancedBackgroundContentForm(forms.ModelForm):
    """Улучшенная форма для управления фоновым контентом"""
    
    # Поля для видео
    video_url = forms.URLField(
        required=False,
        widget=UnfoldAdminTextInputWidget(attrs={
            'placeholder': 'https://www.youtube.com/watch?v=... или https://vimeo.com/...',
            'class': 'vLargeTextField'
        }),
        label='URL видео',
        help_text='Ссылка на YouTube или Vimeo видео'
    )
    platform = forms.ChoiceField(
        choices=[('youtube', 'YouTube'), ('vimeo', 'Vimeo')],
        required=False,
        initial='youtube',
        widget=UnfoldAdminSelectWidget(),
        label='Платформа'
    )
    autoplay = forms.BooleanField(
        required=False,
        initial=True,
        label='Автовоспроизведение'
    )
    muted = forms.BooleanField(
        required=False,
        initial=True,
        label='Без звука'
    )
    loop = forms.BooleanField(
        required=False,
        initial=True,
        label='Зацикливание'
    )
    
    class Meta:
        model = BackgroundContent
        fields = ['content_type', 'is_active']
        exclude = ['title']


class UnifiedBackgroundContentForm(forms.ModelForm):
    """Унифицированная форма для всех типов фонового контента"""
    
    # Поля для видео
    video_url = forms.URLField(
        required=False,
        widget=UnfoldAdminTextInputWidget(attrs={
            'placeholder': 'https://www.youtube.com/watch?v=... или https://vimeo.com/...',
            'class': 'vLargeTextField'
        }),
        label='URL видео',
        help_text='Ссылка на YouTube или Vimeo видео'
    )
    platform = forms.ChoiceField(
        choices=[('youtube', 'YouTube'), ('vimeo', 'Vimeo')],
        required=False,
        initial='youtube',
        widget=UnfoldAdminSelectWidget(),
        label='Платформа'
    )
    autoplay = forms.BooleanField(
        required=False,
        initial=True,
        label='Автовоспроизведение'
    )
    muted = forms.BooleanField(
        required=False,
        initial=True,
        label='Без звука'
    )
    loop = forms.BooleanField(
        required=False,
        initial=True,
        label='Зацикливание'
    )
    
    class Meta:
        model = BackgroundContent
        fields = ['content_type', 'is_active']
        exclude = ['title']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем CSS классы для полей улучшенной формы
        if 'single_image' in self.fields:
            self.fields['single_image'].widget.attrs.update({'class': 'content-type-field enhanced-field'})
        if 'auto_resize' in self.fields:
            self.fields['auto_resize'].widget.attrs.update({'class': 'content-type-field enhanced-field'})
        
        # Добавляем CSS классы для полей видео
        for fld in ('video_url', 'platform', 'autoplay', 'muted', 'loop'):
            if fld in self.fields:
                existing = self.fields[fld].widget.attrs.get('class', '')
                self.fields[fld].widget.attrs['class'] = (existing + ' video-field content-type-field').strip()
        
        # ---------- ДОБАВЛЕНО: обеспечить классы для новых полей ----------
        for fld in ('image', 'width', 'height', 'scaling_mode'):
            if fld in self.fields:
                existing = self.fields[fld].widget.attrs.get('class', '')
                self.fields[fld].widget.attrs['class'] = (existing + ' image-field content-type-field').strip()
        for fld in ('interval', 'transition_duration'):
            if fld in self.fields:
                existing = self.fields[fld].widget.attrs.get('class', '')
                self.fields[fld].widget.attrs['class'] = (existing + ' slideshow-field content-type-field').strip()
        # ---------- КОНЕЦ ДОБАВЛЕННОГО БЛОКА ----------



class SlideshowImageInlineForSlideshow(TabularInline):
    """Inline для изображений слайдшоу внутри Slideshow админки"""
    model = SlideshowImage
    form = SlideshowImageForm
    extra = 1
    min_num = 1
    max_num = 20
    can_delete = True
    show_change_link = True
    fields = ['image', 'order', 'is_primary', 'image_preview']
    readonly_fields = ['image_preview']
    ordering = ['order']
    verbose_name = "Изображение слайдшоу"
    verbose_name_plural = "Изображения слайдшоу"
    
    def image_preview(self, obj):
        """Предварительный просмотр изображения"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = "Предпросмотр"
    
    class Media:
        css = {
            'all': ('background_content/css/multiple_images.css',)
        }
        js = ('background_content/js/multiple_image_inline.js',)


class SlideshowInline(StackedInline):
    """Inline для настроек слайдшоу"""
    model = Slideshow
    extra = 0
    min_num = 1
    max_num = 1
    can_delete = False
    fields = ['interval', 'transition_duration']





class BackgroundImageInline(TabularInline):
    """Inline для одиночного фонового изображения"""
    model = BackgroundImage
    form = BackgroundImageForm
    extra = 0
    min_num = 1
    max_num = 1
    can_delete = False
    show_change_link = True
    fields = ['image', 'scaling_mode', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Предварительный просмотр изображения"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = "Предпросмотр"
    
    class Media:
        css = {
            'all': ('admin/css/background_image.css',)
        }
        js = ('admin/js/background_image.js',)




@admin.register(BackgroundContent)
class BackgroundContentAdmin(ModelAdmin):
    """Админ-панель для управления фоновым контентом с улучшенной функциональностью"""
    form = UnifiedBackgroundContentForm
    list_display = ('content_type', 'is_active', 'created_at')
    list_filter = ('content_type', 'is_active', 'created_at')
    search_fields = ('content_type',)
    ordering = ('-created_at',)
    
    formfield_overrides = {
        models.CharField: {'widget': UnfoldAdminTextInputWidget},
        models.URLField: {'widget': UnfoldAdminTextInputWidget},
    }
    
    class Media:
        css = {
            'all': ('background_content/css/background_image_inline.css',)
        }
        js = (
            'background_content/js/background_image_inline.js',
            'background_content/js/background_content_admin.js',
        )
    
    # Исправленные fieldsets - только поля модели BackgroundContent и функциональность single_image
    fieldsets = (
        ('Основная информация', {
            'fields': ('content_type', 'is_active')
        }),
        ('Настройки видео', {
            'fields': ('video_url', 'platform', 'autoplay', 'muted', 'loop'),
            'classes': ('collapse', 'video-section'),
            'description': 'Настройки для фонового видео с YouTube или Vimeo'
        }),
    )
    
    def get_inlines(self, request, obj):
        """Динамически определяем инлайны в зависимости от типа контента"""
        # Если объект существует, используем его тип контента
        if obj:
            if obj.content_type == 'slideshow':
                return [SlideshowInline]
            elif obj.content_type == 'image':
                return [BackgroundImageInline]
        else:
            # Для новых объектов показываем все инлайны, они будут скрыты/показаны через JavaScript
            return [BackgroundImageInline, SlideshowInline]
        return []
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение модели для обработки различных типов контента"""
        super().save_model(request, obj, form, change)
        
        # Сохраняем данные в зависимости от типа контента
        if obj.content_type == 'image':
            self._save_image_data(obj, form)
        elif obj.content_type == 'video':
            self._save_video_data(obj, form)
        elif obj.content_type == 'slideshow':
            self._save_slideshow_data(obj, form)
            # Автоматически создаем Slideshow если его нет
            if not hasattr(obj, 'slideshow'):
                Slideshow.objects.create(
                    background_content=obj,
                    interval=form.cleaned_data.get('interval', 5000),
                    transition_duration=form.cleaned_data.get('transition_duration', 1000)
                )
    
    def _save_image_data(self, obj, form):
        """Сохраняет данные для фонового изображения"""
        # Создаем BackgroundImage только если тип контента - 'image'
        if obj.content_type != 'image':
            return
            
        image_data = {
            'width': form.cleaned_data.get('width', 1920),
            'height': form.cleaned_data.get('height', 1080),
            'scaling_mode': form.cleaned_data.get('scaling_mode', 'cover'),
        }
        
        if form.cleaned_data.get('image'):
            image_data['image'] = form.cleaned_data['image']
        
        # Проверяем, существует ли уже BackgroundImage для этого контента
        try:
            background_image = BackgroundImage.objects.get(background_content=obj)
            # Обновляем существующий объект
            for key, value in image_data.items():
                if value:  # Обновляем только если есть значение
                    setattr(background_image, key, value)
            background_image.save()
        except BackgroundImage.DoesNotExist:
            # Создаем новый объект только если есть изображение
            if image_data.get('image'):
                BackgroundImage.objects.create(
                    background_content=obj,
                    **image_data
                )
    
    def _save_slideshow_data(self, obj, form):
        """Сохраняет данные для слайдшоу"""
        # Создаем Slideshow только если тип контента - 'slideshow'
        if obj.content_type != 'slideshow':
            return
            
        slideshow_data = {
            'interval': form.cleaned_data.get('interval', 5000),
            'transition_duration': form.cleaned_data.get('transition_duration', 1000),
        }
        
        slideshow, created = Slideshow.objects.get_or_create(
            background_content=obj,
            defaults=slideshow_data
        )
        
        if not created:
            for key, value in slideshow_data.items():
                setattr(slideshow, key, value)
            slideshow.save()
    
    def _save_video_data(self, obj, form):
        """Сохранение данных видео"""
        # Создаем BackgroundVideo только если тип контента - 'video'
        if obj.content_type != 'video':
            return
            
        video_url = form.cleaned_data.get('video_url')
        platform = form.cleaned_data.get('platform', 'youtube')
        autoplay = form.cleaned_data.get('autoplay', True)
        muted = form.cleaned_data.get('muted', True)
        loop = form.cleaned_data.get('loop', True)
        
        if video_url:
            video_obj, created = BackgroundVideo.objects.get_or_create(
                background_content=obj,
                defaults={
                    'video_url': video_url,
                    'platform': platform,
                    'autoplay': autoplay,
                    'muted': muted,
                    'loop': loop,
                }
            )
            # Если объект уже существует, обновляем его
            if not created:
                video_obj.video_url = video_url
                video_obj.platform = platform
                video_obj.autoplay = autoplay
                video_obj.muted = muted
                video_obj.loop = loop
                video_obj.save()
    

    



class SlideshowAdmin(ModelAdmin):
    """Админ класс для слайдшоу"""
    list_display = ['background_content', 'interval', 'transition_duration', 'images_count']
    list_filter = ['interval', 'transition_duration']
    search_fields = ['background_content__title']
    inlines = [SlideshowImageInlineForSlideshow]
    
    formfield_overrides = {
        models.PositiveIntegerField: {'widget': UnfoldAdminTextInputWidget(attrs={'type': 'number', 'min': '0'})},
    }
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('background_content',),
            'classes': ('tab',)
        }),
        ('Настройки слайдшоу', {
            'fields': ('interval', 'transition_duration'),
            'classes': ('tab',),
            'description': 'Интервал смены в миллисекундах (по умолчанию 5000мс = 5сек). Длительность перехода в миллисекундах (по умолчанию 1000мс = 1сек).'
        }),
    )
    
    def images_count(self, obj):
        """Количество изображений в слайдшоу"""
        return obj.images.count()
    images_count.short_description = "Количество изображений"
    
    def has_add_permission(self, request):
        return False  # Слайдшоу создается автоматически при создании BackgroundContent


# Регистрация моделей
admin.site.register(Slideshow, SlideshowAdmin)

# Остальные модели управляются через инлайны и не нуждаются в отдельной регистрации
