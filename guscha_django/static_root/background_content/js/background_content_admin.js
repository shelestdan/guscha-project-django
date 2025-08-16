// JavaScript для динамического показа/скрытия полей в админ-панели background_content

(function($) {
    'use strict';

    // Функция для показа/скрытия полей в зависимости от типа контента
    function toggleContentFields() {
        var contentType = $('#id_content_type').val();
        var $form = $('.form-horizontal, .change-form, form');
        
        // Удаляем все классы показа полей
        $form.removeClass('show-image-fields show-slideshow-fields show-video-fields');
        
        // Скрываем все поля типов контента
        $('.content-type-field').hide();
        $('.image-fieldset, .slideshow-fieldset, .video-fieldset').hide();
        
        // Показываем поля в зависимости от выбранного типа
        switch(contentType) {
            case 'image':
                $form.addClass('show-image-fields');
                $('.image-field, .image-fieldset').show();
                break;
            case 'slideshow':
                $form.addClass('show-slideshow-fields');
                $('.slideshow-field, .slideshow-fieldset').show();
                break;
            case 'video':
                $form.addClass('show-video-fields');
                $('.video-field, .video-fieldset').show();
                break;
        }
        
        // Управляем инлайнами
        toggleInlines(contentType);
    }
    
    // Функция для показа/скрытия инлайнов в зависимости от типа контента
    function toggleInlines(contentType) {
        // Удаляем все классы инлайнов
        $('.inline-group').removeClass('image-inline slideshow-inline video-inline');
        
        // Добавляем соответствующие классы к инлайнам
         $('.inline-group').each(function() {
             var $group = $(this);
             var title = $group.find('h2').text().toLowerCase();
             var hasBackgroundImage = $group.find('[name*="backgroundimage"]').length > 0;
             var hasSlideshow = $group.find('[name*="slideshow"]').length > 0;
            
            // Определяем тип инлайна и добавляем соответствующий класс
             if (title.includes('фоновые изображения') || title.includes('background image') || hasBackgroundImage) {
                 $group.addClass('image-inline');
             } else if (title.includes('слайдшоу') || title.includes('slideshow') || hasSlideshow) {
                 $group.addClass('slideshow-inline');
             }
        });
    }

    // Функция для добавления классов к полям формы
    function addFieldClasses() {
        // Добавляем классы к полям изображения
        $('[name*="image"], [id*="image"]').closest('.form-row, .field-box').addClass('image-field content-type-field');
        
        // Добавляем классы к полям слайдшоу
        $('[name*="slideshow"], [id*="slideshow"]').closest('.form-row, .field-box').addClass('slideshow-field content-type-field');
        
        // Добавляем классы к полям видео
        $('[name*="video"], [id*="video"]').closest('.form-row, .field-box').addClass('video-field content-type-field');
        
        // Добавляем классы к fieldset'ам
        $('fieldset').each(function() {
            var $fieldset = $(this);
            var legend = $fieldset.find('legend, h2').text().toLowerCase();
            
            if (legend.includes('изображен') || legend.includes('image')) {
                $fieldset.addClass('image-fieldset');
            } else if (legend.includes('слайдшоу') || legend.includes('slideshow')) {
                $fieldset.addClass('slideshow-fieldset');
            } else if (legend.includes('видео') || legend.includes('video')) {
                $fieldset.addClass('video-fieldset');
            }
        });
        
        // Добавляем классы к inline группам
        $('.inline-group').each(function() {
            var $group = $(this);
            var title = $group.find('h2').text().toLowerCase();
            
            if (title.includes('изображен') || title.includes('image')) {
                $group.addClass('image-fieldset');
            } else if (title.includes('слайдшоу') || title.includes('slideshow')) {
                $group.addClass('slideshow-fieldset');
            } else if (title.includes('видео') || title.includes('video')) {
                $group.addClass('video-fieldset');
            }
        });
    }

    // Функция для обработки изменений в полях видео
    // function handleVideoFields
    function handleVideoFields() {
        // Поддерживаем как режим без video_type (URL-only), так и старый режим (url/file)
        var $videoTypeField = $('#id_video_type');
        var $videoUrlField = $('#id_video_url').closest('.form-row, .field-box');
        var $videoFileField = $('#id_video_file').closest('.form-row, .field-box');
    
        // Нет поля video_type — работаем в режиме URL-only
        if (!$videoTypeField.length) {
            $videoUrlField.show();
            if ($videoFileField.length) {
                $videoFileField.hide();
            }
            return;
        }
    
        // Старый режим (если появится video_type)
        function toggleVideoFields() {
            var videoType = $videoTypeField.val();
    
            if (videoType === 'url') {
                $videoUrlField.show();
                if ($videoFileField.length) $videoFileField.hide();
            } else if (videoType === 'file') {
                if ($videoFileField.length) $videoFileField.show();
                $videoUrlField.hide();
            } else {
                // Значение не выбрано — скрываем оба
                $videoUrlField.hide();
                if ($videoFileField.length) $videoFileField.hide();
            }
        }
    
        // Обработчик изменения типа видео
        $videoTypeField.on('change', toggleVideoFields);
    
        // Инициализация при загрузке
        toggleVideoFields();
    }

    // Функция для предварительного просмотра изображений
    function setupImagePreview() {
        $('input[type="file"][accept*="image"]').on('change', function() {
            var file = this.files[0];
            var $preview = $(this).siblings('.image-preview');
            
            if (!$preview.length) {
                $preview = $('<img class="image-preview" alt="Предварительный просмотр">');
                $(this).after($preview);
            }
            
            if (file) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    $preview.attr('src', e.target.result).show();
                };
                reader.readAsDataURL(file);
            } else {
                $preview.hide();
            }
        });
    }

    // function setupValidation
    function setupValidation() {
        $('form').on('submit', function(e) {
            var contentType = $('#id_content_type').val();
            var isValid = true;
            var errorMessage = '';
    
            // Очищаем предыдущие ошибки
            $('.validation-error').remove();
    
            // Валидация в зависимости от типа контента
            switch(contentType) {
                case 'image':
                    if (!$('#id_image').val() && !$('#id_image').attr('src')) {
                        isValid = false;
                        errorMessage = 'Необходимо выбрать изображение';
                        $('#id_image').closest('.form-row').append('<div class="validation-error errorlist"><li>' + errorMessage + '</li></div>');
                    }
                    break;
                case 'slideshow':
                    // Проверяем, что в инлайне слайдшоу есть хотя бы одно изображение (новое или существующее)
                    var hasSlide = false;

                    // Новые выбранные файлы
                    $('.slideshow-fieldset input[type="file"][id*="image"]').each(function() {
                        if (this.files && this.files.length > 0) {
                            hasSlide = true;
                        }
                    });

                    // Существующие файлы (ссылки на уже загруженные изображения)
                    if (!hasSlide) {
                        $('.slideshow-fieldset a').each(function() {
                            var href = $(this).attr('href') || '';
                            if (href.match(/\.(png|jpe?g|gif|webp|bmp|tiff?)$/i)) {
                                hasSlide = true;
                            }
                        });
                    }

                    if (!hasSlide) {
                        isValid = false;
                        errorMessage = 'Добавьте хотя бы одно изображение в слайдшоу';
                        // Пытаемся показать ошибку в области инлайна
                        var $inline = $('.slideshow-fieldset').first();
                        if ($inline.length) {
                            $inline.append('<div class="validation-error errorlist"><li>' + errorMessage + '</li></div>');
                        } else {
                            // fallback
                            $('form').prepend('<div class="validation-error errorlist"><li>' + errorMessage + '</li></div>');
                        }
                    }
                    break;
                case 'video':
                    // Упрощённая валидация: требуется только URL видео
                    if (!$('#id_video_url').val()) {
                        isValid = false;
                        errorMessage = 'Необходимо указать URL видео';
                        $('#id_video_url').closest('.form-row, .field-box').append('<div class="validation-error errorlist"><li>' + errorMessage + '</li></div>');
                    }
                    break;
            }
    
            if (!isValid) {
                e.preventDefault();
                // Прокручиваем к первой ошибке
                $('html, body').animate({
                    scrollTop: $('.validation-error').first().offset().top - 100
                }, 500);
            }
        });
    }

    // Инициализация при загрузке DOM
    $(document).ready(function() {
        // Добавляем классы к полям
        addFieldClasses();
        
        // Настраиваем обработчики
        $('#id_content_type').on('change', toggleContentFields);
        
        // Инициализируем показ полей
        toggleContentFields();
        
        // Настраиваем поля видео
        handleVideoFields();
        
        // Настраиваем предварительный просмотр изображений
        setupImagePreview();
        
        // Настраиваем валидацию
        setupValidation();
        
        // Обработка динамически добавляемых inline форм
        $(document).on('formset:added', function(event, $row) {
            // Переинициализируем для новых строк
            addFieldClasses();
            setupImagePreview();
        });
    });

    // Совместимость с Django Unfold
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).ready(function() {
            // Дублируем инициализацию для Django Unfold
            addFieldClasses();
            $('#id_content_type').on('change', toggleContentFields);
            toggleContentFields();
            handleVideoFields();
            setupImagePreview();
            setupValidation();
        });
    }

})(django.jQuery || jQuery || $);

// Дополнительная инициализация для случаев, когда jQuery загружается позже
if (typeof $ === 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof $ !== 'undefined') {
            // Повторная инициализация, если jQuery стал доступен
            $(document).ready(function() {
                addFieldClasses();
                $('#id_content_type').on('change', toggleContentFields);
                toggleContentFields();
                handleVideoFields();
                setupImagePreview();
                setupValidation();
            });
        }
    });
}