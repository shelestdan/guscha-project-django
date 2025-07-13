from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal
import json


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
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(BaseModel):
    """Модель товара"""
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    short_description = models.TextField(blank=True, null=True, verbose_name='Краткое описание')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Артикул')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='products', verbose_name='Категория')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], 
                              verbose_name='Цена')
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                      verbose_name='Цена для сравнения')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
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
    images = models.TextField(blank=True, null=True, verbose_name='Дополнительные изображения (JSON)')
    
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
    
    def get_images(self):
        """Получение дополнительных изображений из JSON"""
        if self.images:
            try:
                return json.loads(self.images)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
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
                                     verbose_name='Максимальное количество для заказа')
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
    image_url = models.URLField(max_length=500, verbose_name='URL изображения')
    alt_text = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt текст')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    is_primary = models.BooleanField(default=False, verbose_name='Основное изображение')
    
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['sort_order']
    
    def __str__(self):
        return f"Изображение для {self.product.name}"


class ProductVariant(BaseModel):
    """Модель варианта товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', 
                              verbose_name='Товар')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Артикул')
    title = models.CharField(max_length=255, verbose_name='Название')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                              verbose_name='Цена')
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                      verbose_name='Цена для сравнения')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
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


class Preorder(BaseModel):
    """Модель предзаказа"""
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    short_description = models.TextField(blank=True, null=True, verbose_name='Краткое описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], 
                              verbose_name='Цена')
    image_url = models.URLField(max_length=500, blank=True, verbose_name='URL основного изображения')
    images = models.TextField(blank=True, null=True, verbose_name='Дополнительные изображения (JSON)')
    start_date = models.DateTimeField(verbose_name='Дата начала')
    end_date = models.DateTimeField(verbose_name='Дата окончания')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_featured = models.BooleanField(default=False, verbose_name='Рекомендуемый')
    meta_title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Meta Title')
    meta_description = models.TextField(blank=True, null=True, verbose_name='Meta Description')
    
    class Meta:
        verbose_name = 'Предзаказ'
        verbose_name_plural = 'Предзаказы'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_images(self):
        """Получение дополнительных изображений из JSON"""
        if self.images:
            try:
                return json.loads(self.images)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @property
    def is_active_now(self):
        """Проверка активности предзаказа по текущей дате"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date


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
