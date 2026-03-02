// JavaScript для улучшенного управления множественными изображениями слайдшоу

(function($) {
    'use strict';

    function setupMultipleImageInline() {
        // Обработка чекбоксов is_primary - только один может быть активным
        $(document).on('change', '.primary-checkbox', function() {
            if ($(this).is(':checked')) {
                // Снимаем галочки с остальных чекбоксов
                $('.primary-checkbox').not(this).prop('checked', false);
            }
        });

        // Автоматическое обновление порядка при добавлении новых элементов
        $(document).on('formset:added', function(event, $row) {
            var $orderInput = $row.find('input[name*="order"], input[name*="ORDER"]');
            if ($orderInput.length) {
                var maxOrder = 0;
                $('input[name*="order"], input[name*="ORDER"]').each(function() {
                    var value = parseInt($(this).val()) || 0;
                    if (value > maxOrder) {
                        maxOrder = value;
                    }
                });
                $orderInput.val(maxOrder + 1);
            }
            
            // Добавляем handle для сортировки к новой строке
            if (!$row.find('.sort-handle').length) {
                $row.prepend('<div class="sort-handle" title="Перетащите для изменения порядка"><i class="fas fa-grip-vertical"></i></div>');
            }
            
            // Обновляем сортировку для включения новой строки
            if ($.fn.sortable && $('.multiple-image-inline .tabular').hasClass('ui-sortable')) {
                $('.multiple-image-inline .tabular').sortable('refresh');
            }
        });

        // Улучшенный предварительный просмотр изображений с информацией о файле
        $(document).on('change', '.slideshow-image-upload', function() {
            var file = this.files[0];
            var $container = $(this).closest('.form-row');
            var $preview = $container.find('.image-preview-container');
            
            if (!$preview.length) {
                $preview = $('<div class="image-preview-container"></div>');
                $(this).after($preview);
            }
            
            if (file) {
                // Проверка типа файла
                if (!file.type.startsWith('image/')) {
                    $preview.html('<div class="error-message">Пожалуйста, выберите файл изображения</div>');
                    return;
                }
                
                // Проверка размера файла (максимум 10MB)
                if (file.size > 10 * 1024 * 1024) {
                    $preview.html('<div class="error-message">Размер файла не должен превышать 10MB</div>');
                    return;
                }
                
                var reader = new FileReader();
                reader.onload = function(e) {
                    var img = new Image();
                    img.onload = function() {
                        var fileSize = (file.size / 1024).toFixed(1) + ' KB';
                        if (file.size > 1024 * 1024) {
                            fileSize = (file.size / (1024 * 1024)).toFixed(1) + ' MB';
                        }
                        
                        $preview.html(`
                            <div class="image-preview-wrapper">
                                <img class="image-preview" src="${e.target.result}" alt="Предварительный просмотр">
                                <div class="image-info">
                                    <div class="file-name">${file.name}</div>
                                    <div class="file-details">${img.width}x${img.height} • ${fileSize}</div>
                                </div>
                            </div>
                        `);
                    };
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
            } else {
                $preview.empty();
            }
        });

        // Drag and Drop функциональность
        setupDragAndDrop();
        
        // Массовая загрузка изображений
        setupBulkUpload();
        
        // Сортировка изображений drag and drop
        setupSortable();
        
        // Валидация формы
        setupFormValidation();
    }

    function setupDragAndDrop() {
        // Добавляем зону для drag and drop
        var $dropZone = $('<div class="bulk-upload-zone">' +
            '<div class="drop-zone-content">' +
                '<i class="fas fa-cloud-upload-alt"></i>' +
                '<h4>Перетащите изображения сюда</h4>' +
                '<p>или <button type="button" class="btn btn-outline-primary bulk-select-btn">выберите файлы</button></p>' +
                '<input type="file" class="bulk-file-input" multiple accept="image/*" style="display: none;">' +
            '</div>' +
        '</div>');
        
        $('.multiple-image-inline').prepend($dropZone);
        
        // Обработка drag and drop событий
        $dropZone.on('dragover dragenter', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).addClass('drag-over');
        });
        
        $dropZone.on('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).removeClass('drag-over');
        });
        
        $dropZone.on('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).removeClass('drag-over');
            
            var files = e.originalEvent.dataTransfer.files;
            handleBulkFiles(files);
        });
        
        // Обработка клика по кнопке выбора файлов (с делегированием событий)
        $(document).on('click', '.bulk-select-btn', function() {
            $('.bulk-file-input').click();
        });
        
        $(document).on('change', '.bulk-file-input', function() {
            handleBulkFiles(this.files);
        });
    }

    function setupBulkUpload() {
        // Функция обработки множественных файлов уже включена в setupDragAndDrop
    }

    function handleBulkFiles(files) {
        var imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        
        if (imageFiles.length === 0) {
            alert('Пожалуйста, выберите файлы изображений');
            return;
        }
        
        // Проверяем, не превышает ли количество файлов лимит
        var currentRows = $('.multiple-image-inline .form-row:not(.empty-form)').length;
        var maxRows = 20; // Максимум из модели
        
        if (currentRows + imageFiles.length > maxRows) {
            alert(`Можно загрузить максимум ${maxRows} изображений. Сейчас: ${currentRows}, выбрано: ${imageFiles.length}`);
            return;
        }
        
        // Добавляем новые строки для каждого файла
        imageFiles.forEach(function(file, index) {
            // Находим кнопку добавления строки
            var $addButton = $('.multiple-image-inline .add-row a, .multiple-image-inline .addlink');
            if ($addButton.length) {
                $addButton.click();
                
                // Ждем, пока строка будет добавлена, затем устанавливаем файл
                setTimeout(function() {
                    var $newRow = $('.multiple-image-inline .form-row:not(.empty-form)').last();
                    var $fileInput = $newRow.find('input[type="file"]');
                    
                    if ($fileInput.length) {
                        // Создаем новый FileList с одним файлом
                        try {
                            var dt = new DataTransfer();
                            dt.items.add(file);
                            $fileInput[0].files = dt.files;
                            
                            // Триггерим событие change для предварительного просмотра
                            $fileInput.trigger('change');
                        } catch (e) {
                            console.warn('Не удалось установить файл программно:', e);
                        }
                    }
                }, 100 * (index + 1));
            } else {
                console.warn('Кнопка добавления строки не найдена');
            }
        });
    }

    function setupSortable() {
        // Делаем строки сортируемыми
        if ($.fn.sortable) {
            $('.multiple-image-inline .tabular').sortable({
                items: '.form-row:not(.add-row)',
                handle: '.sort-handle',
                update: function() {
                    // Обновляем порядок после сортировки
                    $(this).find('.form-row:not(.add-row)').each(function(index) {
                        $(this).find('input[name*="order"], input[name*="ORDER"]').val(index + 1);
                    });
                }
            });
            
            // Добавляем handle для сортировки к каждой строке
            $('.multiple-image-inline .form-row:not(.add-row)').each(function() {
                if (!$(this).find('.sort-handle').length) {
                    $(this).prepend('<div class="sort-handle" title="Перетащите для изменения порядка"><i class="fas fa-grip-vertical"></i></div>');
                }
            });
        }
    }

    function setupFormValidation() {
        // Валидация - как минимум одно изображение должно быть primary
        $('form').on('submit', function(e) {
            var hasPrimary = $('.primary-checkbox:checked').length > 0;
            var hasImages = $('.slideshow-image-upload').filter(function() {
                return $(this).val() || $(this).data('current-file');
            }).length > 0;

            if (hasImages && !hasPrimary) {
                alert('Необходимо выбрать основное изображение для слайдшоу');
                e.preventDefault();
                return false;
            }
        });
    }

    // Инициализация
    $(document).ready(function() {
        setupMultipleImageInline();
    });

    // Совместимость с Django Unfold
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).ready(function() {
            setupMultipleImageInline();
        });
    }

})(django.jQuery || jQuery || $);