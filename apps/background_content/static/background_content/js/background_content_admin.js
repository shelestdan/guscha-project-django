(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Функция для показа/скрытия полей в зависимости от типа контента
        function toggleContentFields() {
            var contentType = $('#id_content_type').val();
            
            // Скрываем все fieldset'ы с настройками
            $('.image-fieldset, .slideshow-fieldset, .video-fieldset').hide();
            
            // Показываем нужный fieldset в зависимости от типа
            if (contentType === 'image') {
                $('.image-fieldset').show();
            } else if (contentType === 'slideshow') {
                $('.slideshow-fieldset').show();
            } else if (contentType === 'video') {
                $('.video-fieldset').show();
            }
        }
        
        // Инициализация при загрузке страницы
        toggleContentFields();
        
        // Обработчик изменения типа контента
        $('#id_content_type').change(function() {
            toggleContentFields();
        });
        
        // Дополнительная логика для валидации полей
        $('form').submit(function(e) {
            var contentType = $('#id_content_type').val();
            var isValid = true;
            var errorMessage = '';
            
            // Валидация в зависимости от типа контента
            if (contentType === 'image') {
                if (!$('#id_image').val()) {
                    isValid = false;
                    errorMessage = 'Для типа "Изображение" необходимо загрузить файл изображения.';
                }
            } else if (contentType === 'video') {
                if (!$('#id_video_url').val()) {
                    isValid = false;
                    errorMessage = 'Для типа "Видео" необходимо указать URL видео.';
                }
            }
            
            if (!isValid) {
                e.preventDefault();
                alert(errorMessage);
                return false;
            }
        });
        
        // Автоматическое определение платформы видео по URL
        $('#id_video_url').blur(function() {
            var url = $(this).val();
            if (url) {
                if (url.includes('youtube.com') || url.includes('youtu.be')) {
                    $('#id_platform').val('youtube');
                } else if (url.includes('vimeo.com')) {
                    $('#id_platform').val('vimeo');
                }
            }
        });
        
        // Предварительный просмотр изображения
        $('#id_image').change(function() {
            var file = this.files[0];
            if (file) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    // Удаляем предыдущий превью если есть
                    $('.image-preview').remove();
                    
                    // Создаем новый превью
                    var preview = $('<div class="image-preview" style="margin-top: 10px;">' +
                        '<img src="' + e.target.result + '" style="max-width: 300px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;" />' +
                        '<p style="font-size: 12px; color: #666; margin-top: 5px;">Предварительный просмотр изображения</p>' +
                        '</div>');
                    
                    $('#id_image').parent().append(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    });
})(django.jQuery);