from rest_framework import serializers
import json
from .models import (
    Category, Product, ProductImage, ProductSize, ProductColor,
    ProductVariant, ProductReview, Preorder, PreorderSize, PreorderColor, Wishlist
)


class BaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор с общей функциональностью"""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ProductSerializer(BaseSerializer):
    """Сериализатор для товаров (базовая версия)"""
    category_name = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'sku', 'category',
            'category_name', 'price', 'compare_price', 'is_active',
            'primary_image', 'created_at', 'updated_at'
        ]
    
    def get_category_name(self, obj):
        """Получение названия категории"""
        return obj.category.name if obj.category else None
    
    def get_primary_image(self, obj):
        """Получение основного изображения товара"""
        if obj.image_url:
            return obj.image_url
        
        primary_image = obj.product_images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.get_image_url
        
        first_image = obj.product_images.first()
        if first_image:
            return first_image.get_image_url
        
        return None


class CategorySerializer(BaseSerializer):
    """Сериализатор для категорий товаров"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'image_url',
            'is_active', 'sort_order', 'product_count', 'created_at', 'updated_at'
        ]
    
    def get_product_count(self, obj):
        """Получение количества активных товаров в категории"""
        return obj.products.filter(is_active=True).count()


class CategoryListSerializer(BaseSerializer):
    """Упрощенный сериализатор для списка категорий"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image_url']


class ProductImageSerializer(BaseSerializer):
    """Сериализатор для изображений товара"""
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'alt_text', 'sort_order', 'is_primary']


class ProductSizeSerializer(BaseSerializer):
    """Сериализатор для размеров товара"""
    class Meta:
        model = ProductSize
        fields = [
            'id', 'size_name', 'size_label', 'stock_quantity', 'max_quantity',
            'is_active', 'is_sold_out', 'is_available'
        ]


class ProductColorSerializer(BaseSerializer):
    """Сериализатор для цветов товара"""
    class Meta:
        model = ProductColor
        fields = [
            'id', 'name', 'hex_code', 'stock_quantity', 'is_active', 'is_available'
        ]


class ProductVariantSerializer(BaseSerializer):
    """Сериализатор для вариантов товара"""
    variant_options = serializers.JSONField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'title', 'price', 'compare_price', 'cost_price',
            'weight', 'stock_quantity', 'is_active', 'variant_options'
        ]


class ProductReviewSerializer(BaseSerializer):
    """Сериализатор для отзывов о товаре"""
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'user', 'user_name', 'rating', 'title', 'content',
            'is_verified_purchase', 'is_approved', 'helpful_count', 'created_at'
        ]
    
    def get_user_name(self, obj):
        """Получение имени пользователя"""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "Анонимный пользователь"


class ProductListSerializer(BaseSerializer):
    """Сериализатор для списка товаров с дополнительными полями"""
    category_name = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()
    in_wishlist = serializers.SerializerMethodField()
    sizes = ProductSizeSerializer(many=True, read_only=True)
    colors = ProductColorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'sku', 'category',
            'category_name', 'price', 'compare_price', 'is_active', 'is_featured',
            'primary_image', 'average_rating', 'review_count', 'is_in_stock', 'in_wishlist',
            'sizes', 'colors'
        ]
    
    def get_category_name(self, obj):
        """Получение названия категории"""
        return obj.category.name if obj.category else None
    
    def get_primary_image(self, obj):
        """Получение основного изображения товара"""
        if obj.image_url:
            return obj.image_url
        
        primary_image = obj.product_images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.get_image_url
        
        first_image = obj.product_images.first()
        if first_image:
            return first_image.get_image_url
        
        return None
        
    def get_average_rating(self, obj):
        """Получение среднего рейтинга товара"""
        try:
            reviews = obj.reviews.filter(is_approved=True)
            if not reviews.exists():
                return 0.0
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        except Exception:
            return 0.0
    
    def get_review_count(self, obj):
        """Получение количества отзывов"""
        try:
            return obj.reviews.filter(is_approved=True).count()
        except Exception:
            return 0
    
    def get_is_in_stock(self, obj):
        """Проверка наличия товара на складе"""
        try:
            if not obj.track_inventory:
                return True
            return obj.stock_quantity > 0 or obj.allow_backorder
        except Exception:
            return False
    
    def get_average_rating(self, obj):
        """Получение среднего рейтинга товара"""
        try:
            reviews = obj.reviews.filter(is_approved=True)
            if not reviews.exists():
                return 0.0
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        except Exception:
            return 0.0
    
    def get_review_count(self, obj):
        """Получение количества отзывов"""
        try:
            return obj.reviews.filter(is_approved=True).count()
        except Exception:
            return 0
    
    def get_is_in_stock(self, obj):
        """Проверка наличия товара на складе"""
        try:
            if not obj.track_inventory:
                return True
            return obj.stock_quantity > 0 or obj.allow_backorder
        except Exception:
            return False
    
    def get_average_rating(self, obj):
        """Получение среднего рейтинга товара"""
        try:
            reviews = obj.reviews.filter(is_approved=True)
            if not reviews.exists():
                return 0.0
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        except Exception:
            return 0.0
    
    def get_review_count(self, obj):
        """Получение количества отзывов о товаре"""
        try:
            return obj.reviews.filter(is_approved=True).count()
        except Exception:
            return 0
    
    def get_is_in_stock(self, obj):
        """Проверка наличия товара на складе"""
        try:
            if not obj.track_inventory:
                return True
            return obj.stock_quantity > 0
        except Exception:
            return False
    
    def get_in_wishlist(self, obj):
        """Проверка, находится ли товар в списке желаний пользователя"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.wishlist_set.filter(user=request.user).exists()
        return False


class ProductDetailSerializer(BaseSerializer):
    """Сериализатор для детальной информации о товаре"""
    category_name = serializers.SerializerMethodField()
    product_images = serializers.SerializerMethodField()
    sizes = ProductSizeSerializer(many=True, read_only=True)
    colors = ProductColorSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()
    in_wishlist = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description', 'sku',
            'category', 'category_name', 'price', 'compare_price', 'cost_price',
            'weight', 'dimensions', 'is_active', 'is_featured', 'requires_shipping',
            'is_digital', 'stock_quantity', 'low_stock_threshold', 'track_inventory',
            'allow_backorder', 'meta_title', 'meta_description', 'search_keywords',
            'image_url', 'product_images', 'sizes', 'colors', 'variants', 'reviews', 'average_rating',
            'review_count', 'is_in_stock', 'in_wishlist', 'created_at', 'updated_at'
        ]
    
    def get_category_name(self, obj):
        """Получение названия категории"""
        return obj.category.name if obj.category else None
    
    def get_product_images(self, obj):
        """Получение всех изображений товара через новую модель ProductImage"""
        images = []
        
        # Добавление основного изображения, если оно есть
        if obj.image_url:
            images.append({
                'id': 'main',
                'image_url': obj.image_url,
                'alt_text': obj.name,
                'is_primary': True,
                'image_type': 'primary'
            })
        
        # Добавление изображений из связанной модели ProductImage
        product_images = obj.product_images.all().order_by('sort_order')
        if product_images.exists():
            for img in product_images:
                image_url = img.get_image_url
                if image_url:  # Добавляем только если URL существует
                    images.append({
                        'id': img.id,
                        'image_url': image_url,
                        'alt_text': img.alt_text or obj.name,
                        'is_primary': img.is_primary,
                        'image_type': img.image_type
                    })
        
        return images


    def get_reviews(self, obj):
        """Получение одобренных отзывов о товаре"""
        reviews = obj.reviews.filter(is_approved=True)[:5]  # Ограничение до 5 отзывов
        return ProductReviewSerializer(reviews, many=True).data
        
    def get_average_rating(self, obj):
        """Получение среднего рейтинга товара"""
        try:
            # Проверяем, есть ли аннотированное значение
            if hasattr(obj, 'avg_rating_annotated') and obj.avg_rating_annotated is not None:
                return round(obj.avg_rating_annotated, 1)
            
            # Если нет, вычисляем вручную
            reviews = obj.reviews.filter(is_approved=True)
            if not reviews.exists():
                return 0.0
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        except Exception:
            return 0.0
    
    def get_review_count(self, obj):
        """Получение количества отзывов"""
        try:
            # Проверяем, есть ли аннотированное значение
            if hasattr(obj, 'review_count_annotated'):
                return obj.review_count_annotated
            
            # Если нет, вычисляем вручную
            return obj.reviews.filter(is_approved=True).count()
        except Exception:
            return 0
    
    def get_is_in_stock(self, obj):
        """Проверка наличия товара на складе"""
        try:
            if not obj.track_inventory:
                return True
            return obj.stock_quantity > 0 or obj.allow_backorder
        except Exception:
            return False
    
    def get_in_wishlist(self, obj):
        """Проверка, находится ли товар в списке желаний пользователя"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.wishlist_set.filter(user=request.user).exists()
        return False


class ProductCreateSerializer(BaseSerializer):
    """Сериализатор для создания товара"""
    slug = serializers.SlugField(required=False)
    additional_images = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        write_only=True
    )
    sizes = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'short_description', 'sku',
            'category', 'price', 'compare_price', 'cost_price', 'weight',
            'dimensions', 'is_active', 'is_featured', 'requires_shipping',
            'is_digital', 'stock_quantity', 'low_stock_threshold', 'track_inventory',
            'allow_backorder', 'meta_title', 'meta_description', 'search_keywords',
            'image_url', 'additional_images', 'sizes'
        ]
    
    def create(self, validated_data):
        additional_images = validated_data.pop('additional_images', [])
        sizes_data = validated_data.pop('sizes', [])
        
        # Создание товара
        product = Product.objects.create(**validated_data)
        
        # Дополнительные изображения теперь обрабатываются через ProductImage модель
        # TODO: Реализовать создание ProductImage объектов для additional_images
        
        # Создание размеров товара
        for size_data in sizes_data:
            ProductSize.objects.create(product=product, **size_data)
        
        return product


class ProductUpdateSerializer(BaseSerializer):
    """Сериализатор для обновления товара"""
    slug = serializers.SlugField(required=False)
    additional_images = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'short_description', 'sku',
            'category', 'price', 'compare_price', 'cost_price', 'weight',
            'dimensions', 'is_active', 'is_featured', 'requires_shipping',
            'is_digital', 'stock_quantity', 'low_stock_threshold', 'track_inventory',
            'allow_backorder', 'meta_title', 'meta_description', 'search_keywords',
            'image_url', 'additional_images'
        ]
    
    def update(self, instance, validated_data):
        additional_images = validated_data.pop('additional_images', None)
        
        # Обновление полей товара
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Дополнительные изображения теперь обрабатываются через ProductImage модель
        # TODO: Реализовать обновление ProductImage объектов для additional_images
        
        instance.save()
        return instance


class ProductReviewCreateSerializer(BaseSerializer):
    """Сериализатор для создания отзыва о товаре"""
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'content']


class PreorderSizeSerializer(BaseSerializer):
    """Сериализатор для размеров предзаказа"""
    class Meta:
        model = PreorderSize
        fields = [
            'id', 'size_name', 'size_label', 'stock_quantity',
            'is_active', 'is_sold_out', 'is_available'
        ]


class PreorderColorSerializer(BaseSerializer):
    """Сериализатор для цветов предзаказа"""
    class Meta:
        model = PreorderColor
        fields = [
            'id', 'name', 'hex_code', 'stock_quantity', 'is_active', 'is_available'
        ]


class PreorderListSerializer(BaseSerializer):
    """Сериализатор для списка предзаказов"""
    is_active_now = serializers.BooleanField(read_only=True)
    model_image = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    sizes = PreorderSizeSerializer(many=True, read_only=True)
    colors = PreorderColorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Preorder
        fields = [
            'id', 'name', 'slug', 'short_description', 'price',
            'image_url', 'model_image', 'product_image', 'is_active', 'is_featured', 'is_active_now',
            'sizes', 'colors', 'created_at', 'updated_at'
        ]
    
    def get_model_image(self, obj):
        """Получение изображения модели"""
        return obj.model_image
    
    def get_product_image(self, obj):
        """Получение изображения товара"""
        return obj.product_image


class PreorderDetailSerializer(BaseSerializer):
    """Сериализатор для детальной информации о предзаказе"""
    sizes = PreorderSizeSerializer(many=True, read_only=True)
    colors = PreorderColorSerializer(many=True, read_only=True)
    is_active_now = serializers.BooleanField(read_only=True)
    model_image = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    product_images = serializers.SerializerMethodField()
    
    class Meta:
        model = Preorder
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'price', 'image_url', 'model_image', 'product_image', 'product_images', 'is_active', 'is_featured', 
            'is_active_now', 'meta_title', 'meta_description', 'sizes', 'colors',
            'created_at', 'updated_at'
        ]
    
    def get_model_image(self, obj):
        """Получение изображения модели"""
        return obj.model_image
    
    def get_product_image(self, obj):
        """Получение изображения товара"""
        return obj.product_image
    
    def get_product_images(self, obj):
        """Получение всех изображений предзаказа (основное + дополнительные)"""
        images = []
        
        # Добавляем основное изображение из image_url если есть
        if obj.image_url:
            images.append({
                'id': None,
                'image_url': obj.image_url,
                'alt_text': obj.name,
                'is_primary': True,
                'image_type': 'primary'
            })
        
        # Добавляем изображения из PreorderImage модели
        preorder_images = obj.preorder_images.all().order_by('sort_order')
        for img in preorder_images:
            if img.get_image_url:
                images.append({
                    'id': img.id,
                    'image_url': img.get_image_url,
                    'alt_text': img.alt_text or obj.name,
                    'is_primary': img.is_primary,
                    'image_type': img.image_type
                })
        
        return images
    



class WishlistSerializer(BaseSerializer):
    """Сериализатор для списка желаний"""
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'created_at']
        read_only_fields = ['user']