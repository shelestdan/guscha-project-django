from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from djmoney.models.fields import MoneyField
import json
import logging
import os

# Импортируем валидаторы и утилиты из созданных модулей
from .validators.image_validator import ImageValidator
from .utils.image_utils import ImageProcessor

logger = logging.getLogger(__name__)

# Создаем экземпляры для использования в моделях
image_validator = ImageValidator()
image_processor = ImageProcessor()

# Функция-обертка для обратной совместимости с миграциями
def validate_image_file(image):
    """Обертка для валидации изображений для совместимости с миграциями"""
    return image_validator.validate_image_file(image)


def product_image_upload_path(instance, filename):
    """Генерация пути для загрузки изображений товаров"""
    return image_processor.generate_upload_path('products', filename)


class BaseModel(models.Model):
    """Базовая модель с общими полями для всех моделей"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Category(BaseModel):
    """Модель категории товаров"""
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='children', verbose_name='Родительская категория')
    image_url = models.URLField(max_length=500, blank=True, verbose_name='URL изображения')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # logger.debug(f"Сохранение товара: {self.name}")
        if not self.slug:
            # logger.debug(f"Генерация slug для товара: {self.name}")
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        # logger.debug(f"Товар сохранен с ID: {self.id}")


class Product(BaseModel):
    """Модель товара"""
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    short_description = models.TextField(blank=True, null=True, verbose_name='Краткое описание')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Артикул')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='products', verbose_name='Категория')
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='RUB', 
                      verbose_name='Цена')
    compare_price = MoneyField(max_digits=10, decimal_places=2, default_currency='RUB', 
                             null=True, blank=True, 
                             verbose_name='Цена для сравнения')
    cost_price = MoneyField(max_digits=10, decimal_places=2, default_currency='RUB', 
                          null=True, blank=True, 
                          verbose_name='Себестоимость')
    weight = models.DecimalField(max_digits=8, decimal_places=3, default=0, verbose_name='Вес')
    dimensions = models.TextField(blank=True, null=True, verbose_name='Размеры (JSON)')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_featured = models.BooleanField(default=False, verbose_name='Рекомендуемый')
    requires_shipping = models.BooleanField(default=True, verbose_name='Требует доставки')
    is_digital = models.BooleanField(default=False, verbose_name='Цифровой товар')
    stock_quantity = models.IntegerField(default=0, verbose_name='Количество на складе')
    low_stock_threshold = models.IntegerField(default=5, verbose_name='Порог малого запаса')
    track_inventory = models.BooleanField(default=True, verbose_name='Отслеживать запасы')
    allow_backorder = models.BooleanField(default=False, verbose_name='Разрешить предзаказ')
    meta_title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Meta Title')
    meta_description = models.TextField(blank=True, null=True, verbose_name='Meta Description')
    search_keywords = models.TextField(blank=True, null=True, verbose_name='Ключевые слова для поиска')
    image_url = models.URLField(max_length=500, blank=True, verbose_name='URL основного изображения')
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def primary_image(self):
        """Получение основного изображения товара"""
        primary_image = self.product_images.filter(is_primary=True).first()
        return primary_image or self.product_images.first()
    

    
    @property
    def average_rating(self):
        """Средний рейтинг товара"""
        reviews = self.reviews.filter(is_approved=True)
        if not reviews.exists():
            return 0
        return sum(review.rating for review in reviews) / reviews.count()
    
    @property
    def review_count(self):
        """Количество отзывов"""
        return self.reviews.filter(is_approved=True).count()
    
    @property
    def is_in_stock(self):
        """Проверка наличия товара на складе"""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0 or self.allow_backorder
    
    @property
    def available_sizes(self):
        """Получение доступных размеров товара"""
        return self.sizes.filter(is_active=True)


class ProductSize(BaseModel):
    """Модель размера товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes', 
                              verbose_name='Товар')
    size_name = models.CharField(max_length=50, verbose_name='Название размера')  # S, M, L, XL, XXL, etc.
    size_label = models.CharField(max_length=100, blank=True, null=True, 
                                verbose_name='Метка размера')
    stock_quantity = models.IntegerField(default=0, verbose_name='Количество на складе')
    max_quantity = models.IntegerField(null=True, blank=True, 
                                     verbose_name='Лимит для заказа',
                                     help_text='Максимальное количество данного размера, которое можно добавить в заказ')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_sold_out = models.BooleanField(default=False, verbose_name='Распродано')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    
    class Meta:
        verbose_name = 'Размер товара'
        verbose_name_plural = 'Размеры товаров'
        ordering = ['sort_order']
    
    def __str__(self):
        return f"{self.product.name} - {self.size_name}"
    
    @property
    def is_available(self):
        """Проверка доступности размера"""
        return self.is_active and not self.is_sold_out and self.stock_quantity > 0


class ProductImage(BaseModel):
    """Модель изображения товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images', 
                              verbose_name='Товар')
    image = models.ImageField(
        upload_to=product_image_upload_path, 
        verbose_name='Изображение', 
        blank=True, 
        null=True,
        validators=[
            image_validator.validate_image_file,
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'],
                message='Поддерживаемые форматы: JPG, JPEG, PNG, WebP, GIF'
            )
        ],
        help_text='Поддерживаемые форматы: JPG, JPEG, PNG, WebP, GIF. Максимальный размер: 10MB. Минимальный размер: 100x100px.'
    )
    image_url = models.URLField(max_length=500, blank=True, verbose_name='URL изображения',
                               help_text='Альтернатива загрузке файла - укажите прямую ссылку на изображение')
    alt_text = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt текст',
                               help_text='Описание изображения для поисковых систем и доступности')
    sort_order = models.IntegerField(default=0, blank=True, verbose_name='Порядок сортировки',
                                   help_text='Порядок отображения (меньшее число = выше в списке)')
    is_primary = models.BooleanField(default=False, verbose_name='Основное изображение',
                                   help_text='Отметьте для установки в качестве основного изображения товара')
    image_type = models.CharField(max_length=20, choices=[
        ('model', 'Модель'),
        ('product', 'Товар'),
        ('additional', 'Дополнительное')
    ], default='additional', verbose_name='Тип изображения')
    
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['sort_order']
    
    def __str__(self):
        return f"Изображение для {self.product.name}"
    
    def clean(self):
        """Валидация модели изображения"""
        super().clean()
        
        # Проверяем, что указано либо файл, либо URL
        if not self.image and not self.image_url:
            raise ValidationError({
                '__all__': 'Необходимо указать либо загрузить файл изображения, либо указать URL.'
            })
        
        # Если указаны оба поля, приоритет отдаем загруженному файлу
        if self.image and self.image_url:
            self.image_url = ''  # Очищаем URL если есть загруженный файл
        
        # Валидация URL изображения
        if self.image_url and not self.image:
            import re
            url_pattern = re.compile(
                r'^https?://.*\.(jpg|jpeg|png|gif|webp)(\?.*)?$', 
                re.IGNORECASE
            )
            if not url_pattern.match(self.image_url):
                raise ValidationError({
                    'image_url': 'URL должен вести на изображение с расширением: jpg, jpeg, png, gif, webp'
                })
        
        # Проверяем, что только одно изображение может быть основным для товара
        if self.is_primary and self.product_id:
            existing_primary = ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(pk=self.pk)
            
            if existing_primary.exists():
                # Автоматически снимаем флаг с других изображений
                logger.info(f'Снимаем флаг основного изображения с других изображений товара {self.product.name}')
                existing_primary.update(is_primary=False)
    
    @property
    def get_image_url(self):
        """Получение URL изображения"""
        # Проверяем, что объект сохранен в базе данных
        if self.pk is None:
            logger.debug("ProductImage.get_image_url вызван для несохраненного объекта")
            return None
            
        logger.debug(f"ProductImage.get_image_url вызван для изображения ID: {self.pk}")
        
        if self.image:
            logger.debug(f"Найдено загруженное изображение: {self.image.name}")
            logger.debug(f"Путь к файлу: {self.image.path if hasattr(self.image, 'path') else 'Путь недоступен'}")
            logger.debug(f"URL изображения: {self.image.url}")
            
            # Проверяем существование файла
            if hasattr(self.image, 'path'):
                file_exists = os.path.exists(self.image.path)
                logger.debug(f"Файл существует на диске: {file_exists}")
                if not file_exists:
                    logger.warning(f"Файл изображения не найден: {self.image.path}")
            
            return self.image.url
        elif self.image_url:
            logger.debug(f"Используется URL изображения: {self.image_url}")
            return self.image_url
        
        logger.warning(f"Изображение не найдено для ProductImage ID: {self.pk}")
        return None
    
    def save(self, *args, **kwargs):
        logger.debug(f"ProductImage.save вызван для изображения ID: {self.pk}")
        logger.debug(f"Товар: {self.product.name if self.product else 'Не указан'}")
        logger.debug(f"Загруженное изображение: {self.image.name if self.image else 'Отсутствует'}")
        logger.debug(f"URL изображения: {self.image_url if self.image_url else 'Отсутствует'}")
        logger.debug(f"Основное изображение: {self.is_primary}")
            
        # Если устанавливаем это изображение как основное, убираем флаг у других
        if self.is_primary:
            logger.debug("Убираем флаг основного изображения у других изображений товара")
            self.product.product_images.exclude(pk=self.pk).update(is_primary=False)
        
        # Проверяем наличие изображения перед сохранением
        if self.image:
            logger.debug(f"Сохраняем загруженное изображение: {self.image.name}")
        elif self.image_url:
            logger.debug(f"Сохраняем URL изображения: {self.image_url}")
        else:
            logger.warning("Попытка сохранить ProductImage без изображения и URL")
        
        super().save(*args, **kwargs)
        logger.debug(f"ProductImage сохранено с ID: {self.pk}")
        
        # Обновляем основное изображение товара после сохранения
        if self.is_primary and self.pk is not None:
            image_url = self.get_image_url
            logger.debug(f"Обновляем основное изображение товара: {image_url}")
            self.product.image_url = image_url
            self.product.save(update_fields=['image_url'])
            logger.debug(f"Основное изображение товара обновлено: {self.product.image_url}")


class ProductVariant(BaseModel):
    """Модель варианта товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', 
                              verbose_name='Товар')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Артикул')
    title = models.CharField(max_length=255, verbose_name='Название')
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='RUB', 
                      null=True, blank=True, verbose_name='Цена')
    compare_price = MoneyField(max_digits=10, decimal_places=2, default_currency='RUB', 
                             null=True, blank=True, 
                             verbose_name='Цена для сравнения')
    cost_price = MoneyField(max_digits=10, decimal_places=2, default_currency='RUB', 
                          null=True, blank=True, 
                          verbose_name='Себестоимость')
    weight = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, 
                               verbose_name='Вес')
    stock_quantity = models.IntegerField(default=0, verbose_name='Количество на складе')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    variant_options = models.TextField(verbose_name='Опции варианта (JSON)')  # JSON string
    
    class Meta:
        verbose_name = 'Вариант товара'
        verbose_name_plural = 'Варианты товаров'
    
    def __str__(self):
        return f"{self.product.name} - {self.title}"


class ProductReview(BaseModel):
    """Модель отзыва о товаре"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', 
                              verbose_name='Товар')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name='Пользователь')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, 
                            verbose_name='Заказ')
    rating = models.IntegerField(verbose_name='Рейтинг')
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Заголовок')
    content = models.TextField(blank=True, null=True, verbose_name='Содержание')
    is_verified_purchase = models.BooleanField(default=False, 
                                             verbose_name='Подтвержденная покупка')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен')
    helpful_count = models.IntegerField(default=0, verbose_name='Счетчик полезности')
    
    class Meta:
        verbose_name = 'Отзыв о товаре'
        verbose_name_plural = 'Отзывы о товарах'
        ordering = ['-created_at']
        unique_together = ['product', 'user', 'order']
    
    def __str__(self):
        return f"Отзыв {self.rating}★ на {self.product.name} от {self.user}"


class Wishlist(BaseModel):
    """Модель избранного"""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"Избранное: {self.user} - {self.product.name}"


def preorder_image_upload_path(instance, filename):
    """Генерация пути для загрузки изображений предзаказов"""
    return image_processor.generate_upload_path('preorders', filename)


class Preorder(BaseModel):
    """Модель предзаказа"""
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    short_description = models.TextField(blank=True, null=True, verbose_name='Краткое описание')
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name='Артикул')
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='RUB', 
                      verbose_name='Цена')
    image_url = models.URLField(max_length=500, blank=True, verbose_name='URL основного изображения')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_featured = models.BooleanField(default=False, verbose_name='Рекомендуемый')
    meta_title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Meta Title')
    meta_description = models.TextField(blank=True, null=True, verbose_name='Meta Description')
    
    class Meta:
        verbose_name = 'Предзаказ'
        verbose_name_plural = 'Предзаказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    

    
    @property
    def is_active_now(self):
        """Проверка активности предзаказа по текущей дате"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active
    
    @property
    def primary_image(self):
        """Получение основного изображения предзаказа"""
        primary_image = self.preorder_images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.get_image_url
        return self.image_url
    
    @property
    def model_image(self):
        """Получение изображения модели"""
        model_image = self.preorder_images.filter(image_type='model').first()
        if model_image:
            return model_image.get_image_url
        return None
    
    @property
    def product_image(self):
        """Получение изображения товара"""
        product_image = self.preorder_images.filter(image_type='product').first()
        if product_image:
            return product_image.get_image_url
        return None


class PreorderImage(BaseModel):
    """Модель изображения предзаказа"""
    preorder = models.ForeignKey(Preorder, on_delete=models.CASCADE, related_name='preorder_images', 
                               verbose_name='Предзаказ')
    image = models.ImageField(upload_to=preorder_image_upload_path, blank=True, null=True, 
                            verbose_name='Изображение')
    image_url = models.URLField(max_length=500, blank=True, verbose_name='URL изображения')
    alt_text = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt текст')
    is_primary = models.BooleanField(default=False, verbose_name='Основное изображение')
    image_type = models.CharField(max_length=20, choices=[
        ('model', 'Модель'),
        ('product', 'Товар'),
        ('additional', 'Дополнительное')
    ], default='additional', verbose_name='Тип изображения')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    
    class Meta:
        verbose_name = 'Изображение предзаказа'
        verbose_name_plural = 'Изображения предзаказов'
        ordering = ['sort_order']
    
    def __str__(self):
        return f"Изображение для {self.preorder.name}"
    
    def get_additional_images(self):
        """Получение дополнительных изображений"""
        return self.preorder.preorder_images.filter(image_type='additional').exclude(pk=self.pk)
    
    def get_all_images_by_type(self, image_type):
        """Получение всех изображений по типу"""
        return self.preorder.preorder_images.filter(image_type=image_type)
    
    def clean(self):
        """Валидация модели"""
        from django.core.exceptions import ValidationError
        
        # Проверяем, что указано либо изображение, либо URL
        if not self.image and not self.image_url:
            raise ValidationError('Необходимо указать либо изображение, либо URL изображения')
        
        # Проверяем, что не указаны одновременно изображение и URL
        if self.image and self.image_url:
            raise ValidationError('Нельзя указывать одновременно изображение и URL')
    
    @property
    def get_image_url(self):
        """Получение URL изображения"""
        if self.image:
            return self.image.url
        return self.image_url
    
    def save(self, *args, **kwargs):
        """Переопределение метода сохранения"""
        # Если устанавливаем это изображение как основное, убираем флаг у других
        if self.is_primary:
            self.preorder.preorder_images.exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
        
        # Обновляем основное изображение предзаказа после сохранения
        if self.is_primary and self.pk is not None:
            self.preorder.image_url = self.get_image_url
            self.preorder.save(update_fields=['image_url'])


class PreorderSize(BaseModel):
    """Модель размера для предзаказа"""
    preorder = models.ForeignKey(Preorder, on_delete=models.CASCADE, related_name='sizes', 
                               verbose_name='Предзаказ')
    size_name = models.CharField(max_length=50, verbose_name='Название размера')
    size_label = models.CharField(max_length=100, blank=True, null=True, 
                                verbose_name='Метка размера')
    stock_quantity = models.IntegerField(default=0, verbose_name='Количество на складе')
    max_quantity = models.IntegerField(null=True, blank=True, 
                                     verbose_name='Максимальное количество для заказа')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_sold_out = models.BooleanField(default=False, verbose_name='Распродано')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    
    class Meta:
        verbose_name = 'Размер предзаказа'
        verbose_name_plural = 'Размеры предзаказов'
        ordering = ['sort_order']
    
    def __str__(self):
        return f"{self.preorder.name} - {self.size_name}"
    
    @property
    def is_available(self):
        """Проверка доступности размера"""
        return self.is_active and not self.is_sold_out and self.stock_quantity > 0 and self.preorder.is_active_now
