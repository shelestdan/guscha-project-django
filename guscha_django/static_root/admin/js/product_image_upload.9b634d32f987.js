(function($) {
    'use strict';
    
    // Функция для инициализации улучшений загрузки изображений
    function initImageUploadEnhancements() {
        console.log('Инициализация улучшений загрузки изображений');
        
        // Убираем стрелочки сворачивания для inline изображений
        $('.inline-group .collapse-toggle, .inline-related .collapse-toggle').hide();
        
        // Принудительно разворачиваем все inline блоки
        $('.inline-group, .inline-related').removeClass('collapsed').addClass('expanded');
        $('.inline-group .module, .inline-related .module').show();
        
        // Обработка загрузки файлов
        setupFileUploadHandlers();
        
        // Обработка превью изображений
        setupImagePreview();
        
        // Валидация файлов
        setupFileValidation();
        
        // Drag & Drop функциональность
        setupDragAndDrop();
    }
    
    // Настройка обработчиков загрузки файлов
    function setupFileUploadHandlers() {
        $(document).on('change', 'input[type="file"][name*="image"]', function(e) {
            const file = e.target.files[0];
            const $input = $(this);
            const $row = $input.closest('.form-row, tr');
            
            console.log('Файл выбран:', file ? file.name : 'нет файла');
            
            // Очищаем предыдущие сообщения
            $row.find('.upload-error, .upload-success').remove();
            
            if (file) {
                // Валидация файла
                if (validateFile(file, $input)) {
                    // Показываем превью
                    showImagePreview(file, $row);
                    
                    // Очищаем поле URL если загружен файл
                    $row.find('input[name*="image_url"]').val('');
                    
                    // Показываем сообщение об успехе
                    $input.after('<span class="upload-success">Файл готов к загрузке</span>');
                }
            }
        });
        
        // Обработка изменения URL изображения
        $(document).on('input', 'input[name*="image_url"]', function() {
            const $input = $(this);
            const $row = $input.closest('.form-row, tr');
            const url = $input.val().trim();
            
            // Очищаем предыдущие сообщения
            $row.find('.upload-error, .upload-success').remove();
            
            if (url) {
                // Очищаем поле файла если введен URL
                $row.find('input[type="file"]').val('');
                
                // Показываем превью URL
                showUrlPreview(url, $row);
            }
        });
    }
    
    // Валидация файлов
    function validateFile(file, $input) {
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        const maxSize = 5 * 1024 * 1024; // 5MB
        
        // Проверка типа файла
        if (!allowedTypes.includes(file.type)) {
            showError($input, 'Неподдерживаемый формат файла. Разрешены: JPG, PNG, WebP');
            return false;
        }
        
        // Проверка размера файла
        if (file.size > maxSize) {
            showError($input, 'Файл слишком большой. Максимальный размер: 5MB');
            return false;
        }
        
        return true;
    }
    
    // Показ превью изображения из файла
    function showImagePreview(file, $row) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const $preview = $row.find('.image-preview, img');
            
            if ($preview.length) {
                $preview.attr('src', e.target.result)
                       .removeClass('error')
                       .show();
            } else {
                // Создаем новое превью если его нет
                const $previewContainer = $row.find('td:first, .field-image_preview');
                if ($previewContainer.length) {
                    $previewContainer.html(
                        '<img src="' + e.target.result + '" class="image-preview" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />'
                    );
                }
            }
        };
        
        reader.onerror = function() {
            showError($row.find('input[type="file"]'), 'Ошибка чтения файла');
        };
        
        reader.readAsDataURL(file);
    }
    
    // Показ превью изображения из URL
    function showUrlPreview(url, $row) {
        const $preview = $row.find('.image-preview, img');
        
        if ($preview.length) {
            $preview.attr('src', url)
                   .removeClass('error')
                   .show()
                   .on('error', function() {
                       $(this).addClass('error').hide();
                       showError($row.find('input[name*="image_url"]'), 'Не удалось загрузить изображение по URL');
                   })
                   .on('load', function() {
                       $(this).removeClass('error');
                       $row.find('.upload-error').remove();
                   });
        } else {
            // Создаем новое превью если его нет
            const $previewContainer = $row.find('td:first, .field-image_preview');
            if ($previewContainer.length) {
                const $img = $('<img src="' + url + '" class="image-preview" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />');
                
                $img.on('error', function() {
                    $(this).addClass('error').hide();
                    showError($row.find('input[name*="image_url"]'), 'Не удалось загрузить изображение по URL');
                }).on('load', function() {
                    $(this).removeClass('error');
                    $row.find('.upload-error').remove();
                });
                
                $previewContainer.html($img);
            }
        }
    }
    
    // Настройка превью изображений
    function setupImagePreview() {
        // Обновляем существующие превью при загрузке страницы
        $('.image-preview, .field-image_preview img').each(function() {
            const $img = $(this);
            const src = $img.attr('src');
            
            if (src && src !== '') {
                $img.on('error', function() {
                    $(this).addClass('error')
                           .attr('title', 'Ошибка загрузки изображения')
                           .css({
                               'background-color': '#f8d7da',
                               'border-color': '#dc3545',
                               'color': '#721c24'
                           });
                });
            }
        });
    }
    
    // Drag & Drop функциональность
    function setupDragAndDrop() {
        $(document).on('dragover dragenter', 'input[type="file"][name*="image"]', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).closest('.file-upload, .form-row').addClass('dragover');
        });
        
        $(document).on('dragleave dragend', 'input[type="file"][name*="image"]', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).closest('.file-upload, .form-row').removeClass('dragover');
        });
        
        $(document).on('drop', 'input[type="file"][name*="image"]', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const $input = $(this);
            $input.closest('.file-upload, .form-row').removeClass('dragover');
            
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                $input[0].files = files;
                $input.trigger('change');
            }
        });
    }
    
    // Показ ошибки
    function showError($input, message) {
        $input.siblings('.upload-error').remove();
        $input.after('<span class="upload-error">' + message + '</span>');
    }
    
    // Функция для принудительного разворачивания inline блоков
    function forceExpandInlines() {
        // Убираем все обработчики сворачивания
        $('.collapse-toggle').off('click').hide();
        
        // Принудительно показываем все inline блоки
        $('.inline-group, .inline-related').each(function() {
            $(this).removeClass('collapsed').addClass('expanded');
            $(this).find('.module').show();
        });
        
        // Убираем классы сворачивания
        $('.collapse, .collapsed').removeClass('collapse collapsed');
    }
    
    // Инициализация при загрузке DOM
    $(document).ready(function() {
        console.log('DOM готов, инициализируем улучшения изображений');
        initImageUploadEnhancements();
        forceExpandInlines();
        
        // Повторная инициализация через небольшую задержку для совместимости с django-unfold
        setTimeout(function() {
            forceExpandInlines();
        }, 500);
    });
    
    // Инициализация при добавлении новых inline форм
    $(document).on('formset:added', function(event, $row) {
        console.log('Добавлена новая inline форма');
        initImageUploadEnhancements();
        forceExpandInlines();
    });
    
    // Обработка изменений в формах
    $(document).on('DOMNodeInserted', function(e) {
        if ($(e.target).hasClass('inline-related') || $(e.target).find('.inline-related').length) {
            setTimeout(function() {
                forceExpandInlines();
            }, 100);
        }
    });
    
})(django.jQuery || jQuery);