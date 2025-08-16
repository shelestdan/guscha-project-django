import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import BackgroundContent, BackgroundImage, Slideshow, BackgroundVideo
from .serializers import (
    BackgroundContentSerializer,
    BackgroundImageSerializer,
    SlideshowSerializer,
    BackgroundVideoSerializer,
    SlideshowImageSerializer
)

# Настройка логгера для background_content
logger = logging.getLogger('background_content')


@api_view(['GET'])
@permission_classes([AllowAny])
def get_active_background(request):
    """
    Получить активный фоновый контент с расширенным логированием и поддержкой плейлистов
    """
    logger.info(f"API запрос на получение активного фонового контента от {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    try:
        # Получаем активный контент с поддержкой плейлистов
        active_contents = BackgroundContent.objects.filter(is_active=True)
        
        # Если есть видео с включенным режимом плейлиста, возвращаем их в порядке playlist_order
        playlist_videos = active_contents.filter(
            content_type='video',
            background_video__playlist_mode=True
        )
        if playlist_videos.exists():
            active_content = playlist_videos.order_by('background_video__playlist_order', 'created_at').first()
        else:
            active_content = active_contents.order_by('-created_at').first()
        
        if not active_content:
            logger.warning("Нет активного фонового контента в базе данных")
            return Response({
                'error': 'Нет активного фонового контента',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"Найден активный контент: {active_content.title} (тип: {active_content.content_type})")
        
        # Получаем конкретный тип контента через OneToOneField и передаем контекст
        if active_content.content_type == 'image':
            if hasattr(active_content, 'background_image'):
                content = active_content.background_image
                serializer = BackgroundImageSerializer(content, context={'request': request})
                logger.debug(f"Сериализовано изображение: {content.image.name if content.image else 'None'}")
            else:
                logger.error(f"Связанное изображение не найдено для контента ID: {active_content.id}")
                return Response({
                    'error': 'Связанное изображение не найдено',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
        elif active_content.content_type == 'slideshow':
            if hasattr(active_content, 'slideshow'):
                content = active_content.slideshow
                serializer = SlideshowSerializer(content, context={'request': request})
                logger.debug(f"Сериализован слайдшоу с {content.images.count()} изображениями")
            else:
                logger.error(f"Связанный слайдшоу не найден для контента ID: {active_content.id}")
                return Response({
                    'error': 'Связанный слайдшоу не найден',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
        elif active_content.content_type == 'video':
            if hasattr(active_content, 'background_video'):
                content = active_content.background_video
                serializer = BackgroundVideoSerializer(content, context={'request': request})
                logger.debug(f"Сериализовано видео: {content.video_url}")
            else:
                logger.error(f"Связанное видео не найдено для контента ID: {active_content.id}")
                return Response({
                    'error': 'Связанное видео не найдено',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            logger.error(f"Неизвестный тип контента: {active_content.content_type}")
            return Response({
                'error': 'Неизвестный тип контента',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Успешно возвращен активный фоновый контент: {active_content.title}")
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Критическая ошибка при получении фонового контента: {str(e)}")
        return Response({
            'error': f'Ошибка при получении фонового контента: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BackgroundContentListView(generics.ListAPIView):
    """
    Список всего фонового контента с логированием и поддержкой плейлистов
    """
    serializer_class = BackgroundContentSerializer
    
    def get_queryset(self):
        """
        Возвращает активный фоновый контент с поддержкой плейлистов
        """
        queryset = BackgroundContent.objects.filter(is_active=True)
        
        # Если есть видео с включенным режимом плейлиста, возвращаем их в порядке playlist_order
        playlist_videos = queryset.filter(
            content_type='video',
            background_video__playlist_mode=True
        )
        if playlist_videos.exists():
            return playlist_videos.order_by('background_video__playlist_order', 'created_at')
        
        # Иначе возвращаем обычный порядок
        return queryset.order_by('-created_at')
    
    def get(self, request, *args, **kwargs):
        logger.info(f"API запрос списка фонового контента от {request.META.get('REMOTE_ADDR', 'unknown')}")
        try:
            response = super().get(request, *args, **kwargs)
            logger.info(f"Возвращено {len(response.data)} элементов фонового контента")
            return response
        except Exception as e:
            logger.exception(f"Ошибка при получении списка фонового контента: {str(e)}")
            raise


class BackgroundContentDetailView(generics.RetrieveAPIView):
    """
    Детальная информация о фоновом контенте с логированием
    """
    queryset = BackgroundContent.objects.all()
    serializer_class = BackgroundContentSerializer
    
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        logger.info(f"API запрос детальной информации о контенте ID: {pk} от {request.META.get('REMOTE_ADDR', 'unknown')}")
        try:
            response = super().get(request, *args, **kwargs)
            logger.info(f"Возвращена детальная информация о контенте ID: {pk}")
            return response
        except Exception as e:
            logger.exception(f"Ошибка при получении детальной информации о контенте ID: {pk}: {str(e)}")
            raise


@api_view(['POST'])
def activate_background(request, pk):
    """
    Активировать определенный фоновый контент с расширенным логированием
    """
    logger.info(f"API запрос на активацию фонового контента ID: {pk} от {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    try:
        # Деактивируем все существующие
        previously_active = BackgroundContent.objects.filter(is_active=True)
        previously_active_count = previously_active.count()
        if previously_active_count > 0:
            logger.info(f"Деактивируем {previously_active_count} ранее активных контентов")
            for prev_content in previously_active:
                logger.debug(f"Деактивирован контент: {prev_content.title} (ID: {prev_content.id})")
        previously_active.update(is_active=False)
        
        # Активируем выбранный
        content = get_object_or_404(BackgroundContent, pk=pk)
        logger.info(f"Найден контент для активации: {content.title} (тип: {content.content_type})")
        
        content.is_active = True
        content.save()
        
        logger.info(f"Успешно активирован фоновый контент: {content.title} (ID: {pk})")
        return Response({
            'success': True,
            'message': f'Фоновый контент "{content.title}" активирован',
            'data': {'id': content.pk, 'title': content.title}
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Критическая ошибка при активации контента ID: {pk}: {str(e)}")
        return Response({
            'error': f'Ошибка при активации контента: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_background_images(request):
    """
    Получить все фоновые изображения
    """
    logger.info(f"API запрос списка фоновых изображений от {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    try:
        images = BackgroundImage.objects.select_related('background_content').all()
        serializer = BackgroundImageSerializer(images, many=True, context={'request': request})
        
        logger.info(f"Возвращено {len(serializer.data)} фоновых изображений")
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Ошибка при получении списка фоновых изображений: {str(e)}")
        return Response({
            'error': f'Ошибка при получении фоновых изображений: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_slideshows(request):
    """
    Получить все слайдшоу
    """
    logger.info(f"API запрос списка слайдшоу от {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    try:
        slideshows = Slideshow.objects.select_related('background_content').prefetch_related('images').all()
        serializer = SlideshowSerializer(slideshows, many=True, context={'request': request})
        
        logger.info(f"Возвращено {len(serializer.data)} слайдшоу")
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Ошибка при получении списка слайдшоу: {str(e)}")
        return Response({
            'error': f'Ошибка при получении слайдшоу: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_background_videos(request):
    """
    Получить все фоновые видео
    """
    logger.info(f"API запрос списка фоновых видео от {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    try:
        videos = BackgroundVideo.objects.select_related('background_content').all()
        serializer = BackgroundVideoSerializer(videos, many=True, context={'request': request})
        
        logger.info(f"Возвращено {len(serializer.data)} фоновых видео")
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Ошибка при получении списка фоновых видео: {str(e)}")
        return Response({
            'error': f'Ошибка при получении фоновых видео: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_slideshow_detail(request, pk):
    """
    Получить детальную информацию о слайдшоу
    """
    logger.info(f"API запрос детальной информации о слайдшоу ID: {pk} от {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    try:
        slideshow = get_object_or_404(
            Slideshow.objects.select_related('background_content').prefetch_related('images'),
            pk=pk
        )
        serializer = SlideshowSerializer(slideshow, context={'request': request})
        
        logger.info(f"Возвращена детальная информация о слайдшоу: {slideshow.background_content.title}")
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Ошибка при получении детальной информации о слайдшоу ID: {pk}: {str(e)}")
        return Response({
            'error': f'Ошибка при получении слайдшоу: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)