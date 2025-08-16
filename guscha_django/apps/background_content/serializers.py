from rest_framework import serializers
from .models import BackgroundContent, BackgroundImage, Slideshow, SlideshowImage, BackgroundVideo


class BackgroundContentSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для фонового контента
    """
    embed_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BackgroundContent
        fields = [
            'id', 'title', 'content_type', 'image_url', 'video_url', 
            'video_type', 'platform', 'embed_url', 'autoplay', 'muted', 'loop',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SlideshowImageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для изображений слайдшоу
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SlideshowImage
        fields = ['id', 'image', 'image_url', 'order', 'is_primary', 'width', 'height']
        read_only_fields = ['id']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class BackgroundImageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для одиночных фоновых изображений с включением content_type
    """
    image_url = serializers.SerializerMethodField()
    content_type = serializers.CharField(source='background_content.content_type', read_only=True)
    title = serializers.CharField(source='background_content.title', read_only=True)
    is_active = serializers.BooleanField(source='background_content.is_active', read_only=True)
    
    class Meta:
        model = BackgroundImage
        fields = [
            'id', 'content_type', 'title', 'is_active', 'image', 'image_url', 
            'width', 'height', 'scaling_mode', 'is_primary'
        ]
        read_only_fields = ['id', 'content_type', 'title', 'is_active']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class SlideshowSerializer(serializers.ModelSerializer):
    """
    Сериализатор для слайдшоу с включением content_type
    """
    images = SlideshowImageSerializer(many=True, read_only=True)
    images_count = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    content_type = serializers.CharField(source='background_content.content_type', read_only=True)
    title = serializers.CharField(source='background_content.title', read_only=True)
    is_active = serializers.BooleanField(source='background_content.is_active', read_only=True)
    
    class Meta:
        model = Slideshow
        fields = [
            'id', 'content_type', 'title', 'is_active', 'interval', 'transition_duration', 
            'images', 'images_count', 'primary_image'
        ]
        read_only_fields = ['id', 'content_type', 'title', 'is_active']
    
    def get_images_count(self, obj):
        return obj.images.count()
    
    def get_primary_image(self, obj):
        """Возвращает основное изображение слайдшоу"""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return SlideshowImageSerializer(primary_image, context=self.context).data
        # Если основного нет, возвращаем первое по порядку
        first_image = obj.images.order_by('order').first()
        if first_image:
            return SlideshowImageSerializer(first_image, context=self.context).data
        return None


class BackgroundVideoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для фоновых видео с включением content_type
    """
    embed_url = serializers.SerializerMethodField()
    content_type = serializers.CharField(source='background_content.content_type', read_only=True)
    title = serializers.CharField(source='background_content.title', read_only=True)
    is_active = serializers.BooleanField(source='background_content.is_active', read_only=True)
    
    class Meta:
        model = BackgroundVideo
        fields = [
            'id', 'content_type', 'title', 'is_active', 'video_url', 'embed_url', 
            'platform', 'autoplay', 'muted', 'loop', 'playlist_order', 'playlist_mode'
        ]
        read_only_fields = ['id', 'content_type', 'title', 'is_active']
    
    def get_embed_url(self, obj):
        """
        Генерирует URL для встраивания видео
        """
        if obj.platform == 'youtube':
            # Извлекаем ID видео из URL
            video_id = self._extract_youtube_id(obj.video_url)
            if video_id:
                params = [
                    'controls=0',
                    'showinfo=0', 
                    'rel=0',
                    'modestbranding=1',
                    'iv_load_policy=3',
                    'disablekb=1',
                    'fs=0',
                    'playsinline=1'
                ]
                if obj.autoplay:
                    params.append('autoplay=1')
                if obj.muted:
                    params.append('mute=1')
                if obj.loop:
                    params.append('loop=1')
                    params.append(f'playlist={video_id}')
                
                params_str = '&'.join(params)
                return f'https://www.youtube-nocookie.com/embed/{video_id}?{params_str}'
        
        elif obj.platform == 'vimeo':
            # Извлекаем ID видео из URL
            video_id = self._extract_vimeo_id(obj.video_url)
            if video_id:
                params = []
                if obj.autoplay:
                    params.append('autoplay=1')
                if obj.muted:
                    params.append('muted=1')
                if obj.loop:
                    params.append('loop=1')
                
                params_str = '&'.join(params)
                return f'https://player.vimeo.com/video/{video_id}?{params_str}'
        
        return obj.video_url
    
    def _extract_youtube_id(self, url):
        """
        Извлекает ID видео из YouTube URL
        """
        import re
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _extract_vimeo_id(self, url):
        """
        Извлекает ID видео из Vimeo URL
        """
        import re
        pattern = r'vimeo\.com/(?:.*#|.*/videos/)?([0-9]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None