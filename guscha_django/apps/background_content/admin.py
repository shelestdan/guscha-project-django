from django.contrib import admin
from django.contrib.admin import StackedInline, ModelAdmin, TabularInline
from django.urls import reverse
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
    BackgroundVideo,
    BackgroundVideoItem
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


class UnifiedBackgroundContentForm(forms.ModelForm):
    """Унифицированная форма для всех типов фонового контента"""
    
    content_type = forms.ChoiceField(
        choices=BackgroundContent.CONTENT_TYPES,
        widget=UnfoldAdminSelectWidget(attrs={'class': 'content-type-selector'}),
        label='Тип контента'
    )
    title = forms.CharField(
        max_length=200,
        widget=UnfoldAdminTextInputWidget(attrs={
            'placeholder': 'Введите название фона',
            'class': 'vLargeTextField'
        }),
        label='Название'
    )
    
    # Поля для изображения (оставляем для быстрого создания)
    image = forms.ImageField(
        required=False,
        widget=UnfoldAdminImageFieldWidget(attrs={
            'accept': 'image/jpeg,image/png,image/webp'
        }),
        label='Изображение (для типа "Изображение")'
    )
    width = forms.IntegerField(
        required=False,
        initial=1920,
        widget=UnfoldAdminTextInputWidget(attrs={'type': 'number', 'min': '1'}),
        label='Ширина'
    )
    height = forms.IntegerField(
        required=False,
        initial=1080,
        widget=UnfoldAdminTextInputWidget(attrs={'type': 'number', 'min': '1'}),
        label='Высота'
    )
    scaling_mode = forms.ChoiceField(
        choices=[('cover', 'Покрыть'), ('contain', 'Вместить'), ('stretch', 'Растянуть')],
        required=False,
        initial='cover',
        widget=UnfoldAdminSelectWidget(),
        label='Режим масштабирования'
    )
    
    # Поля для слайдшоу
    interval = forms.IntegerField(
        required=False,
        initial=5000,
        widget=UnfoldAdminTextInputWidget(attrs={'type': 'number', 'min': '1000'}),
        label='Интервал смены (мс)',
        help_text='Интервал между слайдами в миллисекундах'
    )
    transition_duration = forms.IntegerField(
        required=False,
        initial=1000,
        widget=UnfoldAdminTextInputWidget(attrs={'type': 'number', 'min': '100'}),
        label='Длительность перехода (мс)',
        help_text='Длительность анимации перехода в миллисекундах'
    )
    
    class Meta:
        model = BackgroundContent
        fields = ['content_type', 'title', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем CSS классы для полей улучшенной формы
        if 'single_image' in self.fields:
            self.fields['single_image'].widget.attrs.update({'class': 'content-type-field enhanced-field'})
        if 'auto_resize' in self.fields:
            self.fields['auto_resize'].widget.attrs.update({'class': 'content-type-field enhanced-field'})
        
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
    
    def save(self, commit=True):
        """Переопределяем сохранение для корректной обработки всех полей"""
        instance = super().save(commit=False)
        if 'title' in self.cleaned_data:
            instance.title = self.cleaned_data['title']
        if commit:
            instance.save()
        return instance


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
    fields = ['interval', 'transition_duration', 'images_info']
    readonly_fields = ['images_info']
    
    formfield_overrides = {
        models.PositiveIntegerField: {'widget': UnfoldAdminTextInputWidget(attrs={'type': 'number', 'min': '0'})},
    }
    
    def images_info(self, obj):
        """Информация об изображениях слайдшоу с ссылкой на редактирование"""
        if obj and obj.pk:
            images_count = obj.images.count()
            if images_count > 0:
                admin_url = reverse('admin:background_content_slideshow_change', args=[obj.pk])
                return format_html(
                    '<div style="padding: 10px; background: #f8f9fa; border-radius: 4px; border-left: 4px solid #007cba;">'
                    '<strong>Изображений в слайдшоу: {}</strong><br>'
                    '<a href="{}" target="_blank" style="color: #007cba; text-decoration: none; font-weight: 500;">'
                    '📸 Управление изображениями слайдшоу →'
                    '</a>'
                    '</div>',
                    images_count,
                    admin_url
                )
            else:
                admin_url = reverse('admin:background_content_slideshow_change', args=[obj.pk])
                return format_html(
                    '<div style="padding: 10px; background: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">'
                    '<strong>⚠️ Изображения не добавлены</strong><br>'
                    '<a href="{}" target="_blank" style="color: #856404; text-decoration: none; font-weight: 500;">'
                    '➕ Добавить изображения для слайдшоу →'
                    '</a>'
                    '</div>',
                    admin_url
                )
        return "Сохраните объект для управления изображениями"
    images_info.short_description = "Изображения слайдшоу"


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


class BackgroundVideoItemInline(TabularInline):
    """Inline для видео элементов (плейлист)"""
    model = BackgroundVideoItem
    extra = 1
    fields = ['platform', 'video_url', 'file', 'order']
    ordering = ['order']
    verbose_name = "Видео файл/ссылка"
    verbose_name_plural = "Видео файлы и ссылки"
    
    formfield_overrides = {
        models.URLField: {'widget': UnfoldAdminTextInputWidget(attrs={'placeholder': 'https://...'})},
        models.PositiveIntegerField: {'widget': UnfoldAdminTextInputWidget(attrs={'style': 'width: 60px'})},
    }


class BackgroundVideoInline(StackedInline):
    """Inline для настроек видео"""
    model = BackgroundVideo
    extra = 0
    min_num = 1
    max_num = 1
    can_delete = False
    fields = ['autoplay', 'muted', 'loop', 'playlist_mode']
    verbose_name = "Настройки видео (звук/автозапуск)"
    verbose_name_plural = "Настройки видео"


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
    
    # Исправленные fieldsets - только поля модели BackgroundContent и общие настройки
    fieldsets = (
        ('Основная информация', {
            'fields': ('content_type', 'title', 'is_active')
        }),
        ('Быстрые настройки (только для создания)', {
             'fields': ('image', 'width', 'height', 'scaling_mode', 'interval', 'transition_duration'),
             'classes': ('collapse', 'advanced-settings'),
             'description': 'Здесь можно задать начальные настройки. Детальное управление доступно после сохранения.'
        }),
    )
    
    def get_inlines(self, request, obj):
        """Динамически определяем инлайны в зависимости от типа контента"""
        inlines = []
        
        if obj:
            if obj.content_type == 'image':
                inlines.append(BackgroundImageInline)
            elif obj.content_type == 'slideshow':
                inlines.append(SlideshowInline)
            elif obj.content_type == 'video':
                inlines.append(BackgroundVideoInline)
                inlines.append(BackgroundVideoItemInline)
        
        return inlines
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение модели для обработки различных типов контента"""
        super().save_model(request, obj, form, change)
        
        # Сохраняем данные в зависимости от типа контента
        if obj.content_type == 'image':
            self._save_image_data(obj, form)
        elif obj.content_type == 'video':
            self._ensure_video_settings(obj)
        elif obj.content_type == 'slideshow':
            self._save_slideshow_data(obj, form)
    
    def _save_image_data(self, obj, form):
        """Сохраняет данные для фонового изображения"""
        if obj.content_type != 'image': return
        image_data = {
            'width': form.cleaned_data.get('width', 1920),
            'height': form.cleaned_data.get('height', 1080),
            'scaling_mode': form.cleaned_data.get('scaling_mode', 'cover'),
        }
        if form.cleaned_data.get('image'):
            image_data['image'] = form.cleaned_data['image']
        
        BackgroundVideo.objects.filter(background_content=obj).delete() # Очистка видео если сменили тип? Нет, это опасно.
        # Лучше просто GetOrUpdate
        
        bg_image, created = BackgroundImage.objects.get_or_create(background_content=obj)
        for k, v in image_data.items():
            if v: setattr(bg_image, k, v)
        bg_image.save()
    
    def _save_slideshow_data(self, obj, form):
        """Сохраняет данные для слайдшоу"""
        if obj.content_type != 'slideshow': return
        slideshow_data = {
            'interval': form.cleaned_data.get('interval', 5000),
            'transition_duration': form.cleaned_data.get('transition_duration', 1000),
        }
        slideshow, _ = Slideshow.objects.get_or_create(background_content=obj)
        for k, v in slideshow_data.items():
            setattr(slideshow, k, v)
        slideshow.save()
    
    def _ensure_video_settings(self, obj):
        """Гарантирует существование настроек видео"""
        if obj.content_type != 'video': return
        BackgroundVideo.objects.get_or_create(background_content=obj)
    

    



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
