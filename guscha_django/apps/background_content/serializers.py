from rest_framework import serializers
from .models import BackgroundContent, BackgroundImage, Slideshow, SlideshowImage, BackgroundVideo, BackgroundVideoItem


class BackgroundContentSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для фонового контента
    """
    embed_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BackgroundContent
        fields = [
            'id', 'title', 'content_type', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_embed_url(self, obj):
        # Fallback or simple logic if needed
        return ""


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


class BackgroundVideoItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для элемента видео (для плейлиста)
    """
    embed_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BackgroundVideoItem
        fields = ['id', 'platform', 'video_url', 'file', 'order', 'embed_url']

    def get_embed_url(self, obj):
        """Generates embed URL for the item"""
        if obj.platform == 'file' and obj.file:
            # Return relative URL to let the browser usage the current domain/port
            # This avoids issues with internal Docker IPs (127.0.0.1:8000) being leaked
            return obj.file.url

        if obj.platform == 'youtube':
            video_id = self._extract_youtube_id(obj.video_url)
            if video_id:
                # Basic embed params, main control handled by parent settings or frontend
                return f'https://www.youtube-nocookie.com/embed/{video_id}?controls=0&showinfo=0&rel=0&modestbranding=1&enablejsapi=1'
        
        elif obj.platform == 'vimeo':
            video_id = self._extract_vimeo_id(obj.video_url)
            if video_id:
                return f'https://player.vimeo.com/video/{video_id}?background=1'
                
        return obj.video_url

    def _extract_youtube_id(self, url):
        import re
        if not url: return None
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match: return match.group(1)
        return None
    
    def _extract_vimeo_id(self, url):
        import re
        if not url: return None
        pattern = r'vimeo\.com/(?:.*#|.*/videos/)?([0-9]+)'
        match = re.search(pattern, url)
        if match: return match.group(1)
        return None


class BackgroundVideoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для фоновых видео (настройки + список элементов)
    """
    content_type = serializers.CharField(source='background_content.content_type', read_only=True)
    title = serializers.CharField(source='background_content.title', read_only=True)
    is_active = serializers.BooleanField(source='background_content.is_active', read_only=True)
    
    # Items (playlist)
    items = BackgroundVideoItemSerializer(source='background_content.video_items', many=True, read_only=True)
    
    # Legacy fields (kept for backward compatibility if needed, but we rely on items now)
    video_url = serializers.SerializerMethodField() # Return first item's url if available?
    embed_url = serializers.SerializerMethodField() # Return first item's embed if available?
    
    class Meta:
        model = BackgroundVideo
        fields = [
            'id', 'content_type', 'title', 'is_active', 
            'platform', 'autoplay', 'muted', 'loop', 'playlist_order', 'playlist_mode',
            'items', 'video_url', 'embed_url'
        ]
        read_only_fields = ['id', 'content_type', 'title', 'is_active']
    
    def get_video_url(self, obj):
        # Fallback to legacy field OR first item
        if hasattr(obj.background_content, 'video_items') and obj.background_content.video_items.exists():
            return obj.background_content.video_items.first().video_url
        return obj.video_url
        
    def get_embed_url(self, obj):
        # If items exist, get first item embed
        items = obj.background_content.video_items.all().order_by('order')
        if items.exists():
            item_serializer = BackgroundVideoItemSerializer(items.first(), context=self.context)
            return item_serializer.data.get('embed_url')
            
        # Fallback to legacy logic
        return self._legacy_get_embed_url(obj)

    def _legacy_get_embed_url(self, obj):
        if obj.platform == 'file' and obj.file:
            # Return relative URL
            return obj.file.url

        if obj.platform == 'youtube' and obj.video_url:
            video_id = self._extract_youtube_id(obj.video_url)
            if video_id:
                return f'https://www.youtube-nocookie.com/embed/{video_id}?controls=0&showinfo=0&rel=0&autoplay=1&mute=1&loop=1'
        
        elif obj.platform == 'vimeo' and obj.video_url:
            video_id = self._extract_vimeo_id(obj.video_url)
            if video_id:
                return f'https://player.vimeo.com/video/{video_id}?background=1'
        
        return obj.video_url

    def _extract_youtube_id(self, url):
        return BackgroundVideoItemSerializer()._extract_youtube_id(url)
    
    def _extract_vimeo_id(self, url):
        return BackgroundVideoItemSerializer()._extract_vimeo_id(url)