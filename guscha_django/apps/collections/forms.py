from django import forms
from unfold.widgets import (
    UnfoldAdminTextInputWidget, UnfoldAdminTextareaWidget,
    UnfoldAdminImageFieldWidget
)
from .models import CollectionImage
import logging

logger = logging.getLogger(__name__)


class CollectionImageForm(forms.ModelForm):
    """Форма для изображений коллекции с поддержкой загрузки файлов"""
    
    class Meta:
        model = CollectionImage
        fields = ['image', 'image_url', 'alt_text', 'sort_order']
        widgets = {
            'image': UnfoldAdminImageFieldWidget(attrs={
                'accept': 'image/jpeg,image/png,image/webp,image/gif'
            }),
            'image_url': UnfoldAdminTextInputWidget(attrs={
                'placeholder': 'https://example.com/image.jpg'
            }),
            'alt_text': UnfoldAdminTextInputWidget(attrs={
                'placeholder': 'Описание изображения для SEO'
            }),
            'sort_order': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '0',
                'value': '0'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка лейблов
        self.fields['image'].label = 'Загрузить изображение'
        self.fields['image_url'].label = 'URL изображения'
        self.fields['alt_text'].label = 'Alt текст'
        self.fields['sort_order'].label = 'Порядок сортировки'
        
        # Настройка help_text
        self.fields['image'].help_text = 'Загрузите изображение с компьютера (JPG, PNG, WebP)'
        self.fields['image_url'].help_text = 'Или укажите ссылку на изображение в интернете'
        self.fields['alt_text'].help_text = 'Описание изображения для поисковых систем'
        self.fields['sort_order'].help_text = 'Порядок отображения (меньше = раньше)'
        
        # Делаем поля необязательными
        self.fields['image'].required = False
        self.fields['image_url'].required = False
        self.fields['alt_text'].required = False
        self.fields['sort_order'].required = False

    def clean(self):
        logger.debug("CollectionImageForm.clean вызван")
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')
        
        logger.debug(f"Загруженное изображение: {image.name if image else 'Отсутствует'}")
        logger.debug(f"URL изображения: {image_url if image_url else 'Отсутствует'}")
        
        # Проверяем, что указано либо изображение, либо URL
        if not image and not image_url:
            logger.warning("Валидация не прошла: не указано ни изображение, ни URL")
            raise forms.ValidationError(
                'Необходимо указать либо загрузить изображение, либо указать URL изображения.'
            )
        
        if image:
            logger.debug(f"Размер загруженного файла: {image.size} байт")
            
            # Получаем content_type безопасно для разных типов объектов
            content_type = None
            if hasattr(image, 'content_type'):
                content_type = image.content_type
            elif hasattr(image, 'file') and hasattr(image.file, 'content_type'):
                content_type = image.file.content_type
            
            logger.debug(f"Content-Type: {content_type}")
            
            # Проверяем размер файла (максимум 10MB)
            max_size = 10 * 1024 * 1024  # 10MB в байтах
            if image.size > max_size:
                logger.warning(f"Файл слишком большой: {image.size} байт (максимум {max_size})")
                raise forms.ValidationError(
                    f'Размер файла не должен превышать 10MB. Текущий размер: {image.size / (1024*1024):.1f}MB'
                )
        
        return cleaned_data

    def save(self, commit=True):
        logger.debug("CollectionImageForm.save вызван")
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            logger.debug(f"Изображение коллекции сохранено: {instance.pk}")
            
            # Логика автоматического назначения основного изображения удалена
            logger.debug(f"Изображение коллекции сохранено: {instance.pk}")
        
        return instance