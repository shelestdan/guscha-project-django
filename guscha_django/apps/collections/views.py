from django.http import JsonResponse, Http404
from django.views.generic import ListView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Prefetch, Q
from django.conf import settings
from .models import Collection, CollectionImage
import logging

logger = logging.getLogger(__name__)


# Django представления удалены - используется только React фронтенд


@method_decorator(cache_page(60 * 15), name='dispatch')  # Кэш на 15 минут
class CollectionAPIView(ListView):
    """API для получения коллекций (для AJAX)"""
    model = Collection
    
    def get_queryset(self):
        """Получение коллекций с фильтрацией"""
        queryset = Collection.objects.filter(is_active=True)
        
        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search)
            )
        
        # Фильтр по рекомендуемым
        featured = self.request.GET.get('featured')
        if featured == 'true':
            queryset = queryset.filter(featured=True)
        
        return queryset.prefetch_related(
            'images'
        ).order_by('-featured', 'sort_order', '-created_at')
    
    def render_to_response(self, context, **response_kwargs):
        """Возвращаем JSON ответ"""
        collections_data = []
        
        for collection in context['object_list']:
            primary_image = collection.get_primary_image()
            
            # Получаем все изображения коллекции
            images_data = []
            for image in collection.images.filter(is_active=True).order_by('sort_order', 'created_at'):
                images_data.append({
                    'id': image.id,
                    'image': image.get_image_url(),
                    'thumbnail': image.get_image_url(),  # Можно добавить отдельное поле для миниатюр
                    'alt_text': image.alt_text,
                    'caption': image.caption,
                    'is_primary': image.is_primary,
                })
            
            collections_data.append({
                'id': collection.id,
                'name': collection.name,
                'slug': collection.slug,
                'short_description': collection.short_description,
                'description': collection.description,
                'featured': collection.featured,
                'url': collection.get_absolute_url(),
                'primary_image': {
                    'url': primary_image.get_image_url() if primary_image else None,
                    'alt': primary_image.alt_text if primary_image else collection.name,
                } if primary_image else None,
                'images': images_data,
                'images_count': len(images_data),
            })
        
        return JsonResponse({
            'collections': collections_data,
            'count': len(collections_data)
        })


def collection_images_api(request, slug):
    """API для получения изображений коллекции"""
    try:
        collection = get_object_or_404(
            Collection.objects.prefetch_related('images'),
            slug=slug,
            is_active=True
        )
        
        images_data = []
        for image in collection.images.filter(is_active=True).order_by('sort_order', 'created_at'):
            images_data.append({
                'id': image.id,
                'url': image.get_image_url(),
                'alt': image.alt_text,
                'caption': image.caption,
                'is_primary': image.is_primary,
                'width': image.width,
                'height': image.height,
            })
        
        return JsonResponse({
            'collection': {
                'id': collection.id,
                'name': collection.name,
                'slug': collection.slug,
            },
            'images': images_data,
            'count': len(images_data)
        })
    
    except Collection.DoesNotExist:
        return JsonResponse({
            'error': 'Коллекция не найдена'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in collection_images_api: {str(e)}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


# Функциональные представления для совместимости
# Функциональные представления удалены - используется только React фронтенд


# Дополнительные утилиты
def get_featured_collections(limit=6):
    """Получение рекомендуемых коллекций"""
    return Collection.objects.filter(
        is_active=True,
        featured=True
    ).prefetch_related(
        'images'
    ).order_by('sort_order', '-created_at')[:limit]


def get_collection_by_slug(slug):
    """Получение коллекции по slug"""
    try:
        return Collection.objects.prefetch_related(
            'images'
        ).get(slug=slug, is_active=True)
    except Collection.DoesNotExist:
        return None