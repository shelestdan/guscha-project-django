from django import forms
from unfold.widgets import (
    UnfoldAdminTextInputWidget, UnfoldAdminTextareaWidget,
    UnfoldAdminSelectWidget, UnfoldAdminCheckboxSelectMultiple,
    UnfoldAdminImageFieldWidget,
    UnfoldAdminMoneyWidget
)
from .models import ProductSize, Product, ProductImage, ProductColor, PreorderImage, PreorderSize, PreorderColor
import logging

logger = logging.getLogger(__name__)


class ProductForm(forms.ModelForm):
    """Современная форма для товара с улучшенными полями"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'sku', 'category', 'description',
            'price', 'stock_quantity', 
            'track_inventory',
            'is_active',
            'meta_title', 'meta_description'
        ]
        widgets = {
            'name': UnfoldAdminTextInputWidget(),
            'slug': UnfoldAdminTextInputWidget(),
            'sku': UnfoldAdminTextInputWidget(),
            'category': UnfoldAdminSelectWidget(),
            'description': UnfoldAdminTextareaWidget(attrs={'rows': 6}),
            'price': UnfoldAdminMoneyWidget(),
            'stock_quantity': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '0'
            }),

            'meta_title': UnfoldAdminTextInputWidget(attrs={'maxlength': '255'}),
            'meta_description': UnfoldAdminTextareaWidget(attrs={
                'rows': 3,
                'maxlength': '500'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка лейблов
        self.fields['name'].label = 'Название товара'
        self.fields['slug'].label = 'URL (slug)'
        self.fields['sku'].label = 'Артикул'
        self.fields['category'].label = 'Категория'
        self.fields['description'].label = 'Полное описание'
        self.fields['price'].label = 'Цена (₽)'
        self.fields['stock_quantity'].label = 'Количество на складе'

        self.fields['track_inventory'].label = 'Отслеживать запасы'
        self.fields['is_active'].label = 'Активен'
        
        # Настройка help_text
        self.fields['slug'].help_text = 'Автоматически генерируется из названия'
        
        # Делаем некоторые поля необязательными
        optional_fields = [
            'slug'
        ]
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        
        # Проверяем корректность цены
        if price is not None:
            try:
                from djmoney.money import Money
                from decimal import Decimal
                
                # Если price является объектом Money
                if hasattr(price, 'amount'):
                    if price.amount <= Decimal('0'):
                        raise forms.ValidationError({
                            'price': 'Цена должна быть больше 0'
                        })
                else:
                    # Если price не является объектом Money, пытаемся преобразовать
                    try:
                        price_decimal = Decimal(str(price))
                        if price_decimal <= Decimal('0'):
                            raise forms.ValidationError({
                                'price': 'Цена должна быть больше 0'
                            })
                    except (ValueError, TypeError):
                        raise forms.ValidationError({
                            'price': 'Некорректное значение цены'
                        })
            except Exception as e:
                raise forms.ValidationError({
                    'price': f'Ошибка валидации цены: {str(e)}'
                })
        
        return cleaned_data


class ProductColorForm(forms.ModelForm):
    """Форма для цветов товара"""
    
    class Meta:
        model = ProductColor
        fields = ['name', 'hex_code', 'stock_quantity', 'is_active']
        widgets = {
            'name': UnfoldAdminTextInputWidget(attrs={
                'placeholder': 'Например: Черный, Белый, Красный'
            }),
            'hex_code': UnfoldAdminTextInputWidget(attrs={
                'type': 'color',
                'style': 'width: 60px; height: 30px; padding: 0;'
            }),
            'stock_quantity': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '0'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Название цвета'
        self.fields['hex_code'].label = 'Цвет (HEX)'
        self.fields['stock_quantity'].label = 'Количество на складе'
        self.fields['is_active'].label = 'Активен'


class PreorderColorForm(forms.ModelForm):
    """Форма для цветов предзаказа"""
    
    class Meta:
        model = PreorderColor
        fields = ['name', 'hex_code', 'stock_quantity', 'is_active']
        widgets = {
            'name': UnfoldAdminTextInputWidget(attrs={
                'placeholder': 'Например: Черный, Белый, Красный'
            }),
            'hex_code': UnfoldAdminTextInputWidget(attrs={
                'type': 'color',
                'style': 'width: 60px; height: 30px; padding: 0;'
            }),
            'stock_quantity': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '0'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Название цвета'
        self.fields['hex_code'].label = 'Цвет (HEX)'
        self.fields['stock_quantity'].label = 'Количество на складе'
        self.fields['is_active'].label = 'Активен'


class ProductSizeForm(forms.ModelForm):
    """Упрощенная форма для размеров товара"""
    
    class Meta:
        model = ProductSize
        fields = ['size_name', 'stock_quantity', 'max_quantity', 'is_sold_out', 'is_active']
        widgets = {
            'size_name': UnfoldAdminTextInputWidget(attrs={
                'placeholder': 'Например: S, M, L, XL'
            }),
            'stock_quantity': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '0'
            }),
            'max_quantity': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '1',
                'placeholder': 'Лимит для заказа'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['size_name'].label = 'Название размера'
        self.fields['stock_quantity'].label = 'Количество на складе'
        self.fields['max_quantity'].label = 'Лимит для заказа'
        self.fields['is_sold_out'].label = 'Распродано'
        self.fields['is_active'].label = 'Активен'
        
        # Делаем max_quantity необязательным
        self.fields['max_quantity'].required = False


class PreorderSizeForm(forms.ModelForm):
    """Форма для размеров предзаказа"""
    
    class Meta:
        model = PreorderSize
        fields = ['size_name', 'stock_quantity', 'max_quantity', 'is_sold_out', 'is_active']
        widgets = {
            'size_name': UnfoldAdminTextInputWidget(attrs={
                'placeholder': 'Например: S, M, L, XL'
            }),
            'stock_quantity': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '0'
            }),
            'max_quantity': UnfoldAdminTextInputWidget(attrs={
                'type': 'number',
                'min': '1',
                'placeholder': 'Максимум в заказе'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['size_name'].label = 'Название размера'
        self.fields['stock_quantity'].label = 'Количество на складе'
        self.fields['max_quantity'].label = 'Лимит для заказа'
        self.fields['is_sold_out'].label = 'Распродано'
        self.fields['is_active'].label = 'Активен'
        
        # Делаем max_quantity необязательным
        self.fields['max_quantity'].required = False


class ProductImageForm(forms.ModelForm):
    """Форма для изображений товара с поддержкой загрузки файлов"""
    
    class Meta:
        model = ProductImage
        fields = ['image', 'image_url', 'alt_text', 'is_primary', 'sort_order']
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
    
    def clean(self):
        """Валидация формы изображения"""
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')
        
        # Проверяем, что указано либо файл, либо URL
        if not image and not image_url:
            raise forms.ValidationError(
                'Необходимо указать либо загрузить файл изображения, либо указать URL.'
            )
        
        # Проверяем размер файла
        if image and hasattr(image, 'size'):
            if image.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(
                    'Размер файла не должен превышать 10MB.'
                )
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка лейблов
        self.fields['image'].label = 'Загрузить изображение'
        self.fields['image_url'].label = 'URL изображения'
        self.fields['alt_text'].label = 'Alt текст'
        self.fields['is_primary'].label = 'Основное изображение'
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
        # logger.debug("ProductImageForm.clean вызван")
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')
        
        # Проверяем, что указано либо изображение, либо URL
        if not image and not image_url:
            logger.warning("Валидация не прошла: не указано ни изображение, ни URL")
            raise forms.ValidationError(
                'Необходимо указать либо загрузить изображение, либо указать URL изображения.'
            )
        
        if image:
            
            # Получаем content_type безопасно для разных типов объектов
            content_type = None
            if hasattr(image, 'content_type'):
                content_type = image.content_type
            elif hasattr(image, 'file') and hasattr(image.file, 'content_type'):
                content_type = image.file.content_type
            
            if not content_type:
                content_type = 'unknown'
            
            # logger.debug(f"Тип содержимого: {content_type}")
            
            # Проверяем размер файла
            max_size = 10 * 1024 * 1024  # 10MB
            if image.size > max_size:
                logger.warning(f"Файл слишком большой: {image.size} байт (максимум {max_size})")
                raise forms.ValidationError(
                    f'Размер файла не должен превышать 10MB. Текущий размер: {image.size / 1024 / 1024:.1f}MB'
                )
            
            # Проверяем тип файла только если content_type доступен
            if content_type and content_type != 'unknown':
                allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
                if content_type not in allowed_types:
                    logger.warning(f"Неподдерживаемый тип файла: {content_type}")
                    raise forms.ValidationError(
                        f'Неподдерживаемый тип файла: {content_type}. Разрешены: JPEG, PNG, WebP, GIF'
                    )
            else:
                logger.debug("Тип содержимого недоступен, пропускаем проверку типа файла")
        
        logger.debug("Валидация ProductImageForm прошла успешно")
        return cleaned_data
    
    def save(self, commit=True):
        """Сохранение формы изображения товара"""
        # logger.debug("ProductImageForm.save вызван")
        
        instance = super().save(commit=False)
        
        if self.cleaned_data.get('image'):
            logger.debug(f"Сохраняем форму с загруженным изображением: {self.cleaned_data['image'].name}")
        elif self.cleaned_data.get('image_url'):
            logger.debug(f"Сохраняем форму с URL изображения: {self.cleaned_data['image_url']}")
        
        logger.debug(f"Детали instance: pk={instance.pk}, product={getattr(instance, 'product', None)}")
        
        if commit:
            instance.save()
            logger.debug(f"ProductImage сохранено через форму с ID: {instance.pk}")
            
            # После сохранения проверяем, нужно ли установить как основное
            if instance.product and self.cleaned_data.get('image'):
                logger.debug(f"Проверяем новое изображение для товара {instance.product.name}")
                existing_primary = instance.product.product_images.filter(is_primary=True).exists()
                logger.debug(f"Есть ли основное изображение: {existing_primary}")
                if not existing_primary:
                    logger.debug("Устанавливаем новое изображение как основное (первое для товара)")
                    instance.is_primary = True
                    instance.save(update_fields=['is_primary'])
                    logger.debug(f"Изображение {instance.pk} установлено как основное")
                else:
                    logger.debug("У товара уже есть основное изображение, новое не будет основным")
        
        return instance


class PreorderImageForm(forms.ModelForm):
    """Форма для изображений предзаказа с поддержкой загрузки файлов"""
    
    class Meta:
        model = PreorderImage
        fields = ['image', 'image_url', 'alt_text', 'image_type', 'sort_order']
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
    
    def clean(self):
        """Валидация формы изображения предзаказа"""
        logger.debug("PreorderImageForm.clean вызван")
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
            
            if not content_type:
                content_type = 'unknown'
            
            logger.debug(f"Тип содержимого: {content_type}")
            
            # Проверяем размер файла
            max_size = 10 * 1024 * 1024  # 10MB
            if image.size > max_size:
                logger.warning(f"Файл слишком большой: {image.size} байт (максимум {max_size})")
                raise forms.ValidationError(
                    f'Размер файла не должен превышать 10MB. Текущий размер: {image.size / 1024 / 1024:.1f}MB'
                )
            
            # Проверяем тип файла только если content_type доступен
            if content_type and content_type != 'unknown':
                allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
                if content_type not in allowed_types:
                    logger.warning(f"Неподдерживаемый тип файла: {content_type}")
                    raise forms.ValidationError(
                        f'Неподдерживаемый тип файла: {content_type}. Разрешены: JPEG, PNG, WebP, GIF'
                    )
            else:
                logger.debug("Тип содержимого недоступен, пропускаем проверку типа файла")
        
        logger.debug("Валидация PreorderImageForm прошла успешно")
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка лейблов
        self.fields['image'].label = 'Загрузить изображение'
        self.fields['image_url'].label = 'URL изображения'
        self.fields['alt_text'].label = 'Alt текст'
        self.fields['image_type'].label = 'Тип изображения'
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
    
    def save(self, commit=True):
        """Сохранение формы изображения предзаказа"""
        logger.debug("PreorderImageForm.save вызван")
        
        instance = super().save(commit=False)
        
        if self.cleaned_data.get('image'):
            logger.debug(f"Сохраняем форму с загруженным изображением: {self.cleaned_data['image'].name}")
        elif self.cleaned_data.get('image_url'):
            logger.debug(f"Сохраняем форму с URL изображения: {self.cleaned_data['image_url']}")
        
        logger.debug(f"Детали instance: pk={instance.pk}, preorder={getattr(instance, 'preorder', None)}")
        
        if commit:
            instance.save()
            logger.debug(f"PreorderImage сохранено через форму с ID: {instance.pk}")
            
            # После сохранения проверяем, нужно ли установить как основное
            if instance.preorder and self.cleaned_data.get('image'):
                logger.debug(f"Проверяем новое изображение для предзаказа {instance.preorder.name}")
                existing_primary = instance.preorder.preorder_images.filter(is_primary=True).exists()
                logger.debug(f"Есть ли основное изображение: {existing_primary}")
                if not existing_primary:
                    logger.debug("Устанавливаем новое изображение как основное (первое для предзаказа)")
                    instance.is_primary = True
                    instance.save(update_fields=['is_primary'])
                    logger.debug(f"Изображение {instance.pk} установлено как основное")
                else:
                    logger.debug("У предзаказа уже есть основное изображение, новое не будет основным")
        
        return instance