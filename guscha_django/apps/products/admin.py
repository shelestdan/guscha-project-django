from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, ProductImage, ProductSize, 
    ProductVariant, ProductReview, Preorder, PreorderSize, Wishlist
)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order', 'is_active')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image_url', 'alt_text', 'is_primary', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" width="100" height="100" />', obj.image_url)
        return "-"


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('user', 'rating', 'content', 'created_at')
    can_delete = False
    max_num = 0


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'stock_quantity', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'category', 'created_at')
    search_fields = ('name', 'sku', 'description', 'search_keywords')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock_quantity', 'is_active', 'is_featured')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductImageInline, ProductSizeInline, ProductVariantInline, ProductReviewInline]
    fieldsets = (
        ('Основные Данные', {
            'fields': ('name', 'slug', 'sku', 'description')
        }),
        ('Категория и Цена', {
            'fields': ('category', 'price')
        }),
        ('Дополнительная Информация', {
            'classes': ('collapse',),
            'fields': (
                ('weight', 'dimensions'),
                ('is_active', 'is_featured'),
                ('stock_quantity', 'track_inventory', 'allow_backorder'),
                ('meta_title', 'meta_description'),
                'search_keywords'
            )
        }),
        ('История', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    class Media:
        css = {
            'all': ('jazzmin/css/modern_forms.css',)
        }


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__username', 'content')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at',)


class PreorderSizeInline(admin.TabularInline):
    model = PreorderSize
    extra = 1


class PreorderAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PreorderSizeInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'price', 'image_url', 'images')
        }),
        ('Даты', {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at')
        }),
        ('Настройки', {
            'fields': ('is_active',)
        }),
    )


class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at',)


# Регистрация моделей в административной панели
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Preorder, PreorderAdmin)
admin.site.register(Wishlist, WishlistAdmin)
