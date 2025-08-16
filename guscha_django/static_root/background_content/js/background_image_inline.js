/**
 * JavaScript для улучшенного инлайна BackgroundImageInline
 * Обеспечивает drag-and-drop функциональность и управление основными изображениями
 */

(function($) {
    'use strict';

    // Инициализация при загрузке DOM
    $(document).ready(function() {
        initBackgroundImageInline();
    });

    // Инициализация при добавлении новых форм через Django admin
    $(document).on('formset:added', function(event, $row, formsetName) {
        if (formsetName === 'background_images') {
            initBackgroundImageInline();
        }
    });

    function initBackgroundImageInline() {
        setupDragAndDrop();
        setupPrimaryImageHandling();
        setupImagePreview();
        setupFileInputHandling();
    }

    /**
     * Настройка drag-and-drop функциональности
     */
    function setupDragAndDrop() {
        const $inlineGroup = $('.inline-group[data-inline-type="background_content.BackgroundImage"]');
        
        if ($inlineGroup.length === 0) return;

        const $tbody = $inlineGroup.find('.tabular tbody');
        
        if ($tbody.length === 0) return;

        // Делаем строки перетаскиваемыми
        $tbody.sortable({
            items: 'tr.form-row:not(.add-row)',
            handle: '.drag-handle',
            placeholder: 'ui-sortable-placeholder',
            helper: 'clone',
            opacity: 0.7,
            cursor: 'move',
            tolerance: 'pointer',
            start: function(event, ui) {
                ui.placeholder.height(ui.item.height());
                ui.placeholder.html('<td colspan="100%" class="sortable-placeholder">Перетащите сюда</td>');
            },
            update: function(event, ui) {
                updateRowOrder();
            }
        });

        // Добавляем drag handle к каждой строке
        $tbody.find('tr.form-row:not(.add-row)').each(function() {
            const $row = $(this);
            if ($row.find('.drag-handle').length === 0) {
                $row.find('td:first').prepend('<span class="drag-handle" title="Перетащить для изменения порядка">⋮⋮</span>');
            }
        });
    }

    /**
     * Обновление порядка строк после drag-and-drop
     */
    function updateRowOrder() {
        const $rows = $('.inline-group[data-inline-type="background_content.BackgroundImage"] tr.form-row:not(.add-row)');
        
        $rows.each(function(index) {
            const $row = $(this);
            const $orderInput = $row.find('input[name$="-order"]');
            if ($orderInput.length > 0) {
                $orderInput.val(index + 1);
            }
        });
    }

    /**
     * Управление основными изображениями
     */
    function setupPrimaryImageHandling() {
        $(document).on('change', 'input[name$="-is_primary"]', function() {
            const $checkbox = $(this);
            const $inlineGroup = $checkbox.closest('.inline-group');
            
            if ($checkbox.is(':checked')) {
                // Снимаем отметку с других чекбоксов is_primary в той же группе
                $inlineGroup.find('input[name$="-is_primary"]').not($checkbox).prop('checked', false);
                
                // Добавляем визуальный индикатор
                updatePrimaryIndicators($inlineGroup);
            } else {
                updatePrimaryIndicators($inlineGroup);
            }
        });
    }

    /**
     * Обновление визуальных индикаторов основного изображения
     */
    function updatePrimaryIndicators($inlineGroup) {
        $inlineGroup.find('tr.form-row').each(function() {
            const $row = $(this);
            const $checkbox = $row.find('input[name$="-is_primary"]');
            const $indicator = $row.find('.primary-indicator');
            
            if ($checkbox.is(':checked')) {
                $row.addClass('primary-image');
                if ($indicator.length === 0) {
                    $row.find('td:first').append('<span class="primary-indicator" title="Основное изображение">★</span>');
                }
            } else {
                $row.removeClass('primary-image');
                $indicator.remove();
            }
        });
    }

    /**
     * Настройка предварительного просмотра изображений
     */
    function setupImagePreview() {
        $(document).on('change', 'input[type="file"][name$="-image"]', function() {
            const $input = $(this);
            const $row = $input.closest('tr');
            const file = this.files[0];
            
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    let $preview = $row.find('.image-preview');
                    
                    if ($preview.length === 0) {
                        $preview = $('<div class="image-preview"><img src="" alt="Preview" /></div>');
                        $input.after($preview);
                    }
                    
                    $preview.find('img').attr('src', e.target.result);
                    $preview.show();
                };
                
                reader.readAsDataURL(file);
            } else {
                $row.find('.image-preview').hide();
            }
        });
    }

    /**
     * Обработка загрузки файлов
     */
    function setupFileInputHandling() {
        $(document).on('change', 'input[type="file"][name$="-image"]', function() {
            const $input = $(this);
            const $row = $input.closest('tr');
            const fileName = this.files[0] ? this.files[0].name : '';
            
            // Обновляем отображение имени файла
            let $fileName = $row.find('.file-name');
            if ($fileName.length === 0) {
                $fileName = $('<span class="file-name"></span>');
                $input.after($fileName);
            }
            
            $fileName.text(fileName);
            
            // Показываем/скрываем кнопку очистки
            const $clearBtn = $row.find('.file-clear');
            if (fileName) {
                if ($clearBtn.length === 0) {
                    const $clearButton = $('<button type="button" class="file-clear" title="Очистить файл">×</button>');
                    $fileName.after($clearButton);
                }
            } else {
                $clearBtn.remove();
            }
        });

        // Обработка кнопки очистки файла
        $(document).on('click', '.file-clear', function(e) {
            e.preventDefault();
            const $btn = $(this);
            const $row = $btn.closest('tr');
            const $input = $row.find('input[type="file"]');
            
            $input.val('');
            $row.find('.file-name').text('');
            $row.find('.image-preview').hide();
            $btn.remove();
        });
    }

    /**
     * Валидация форм
     */
    function validateForms() {
        const $inlineGroup = $('.inline-group[data-inline-type="background_content.BackgroundImage"]');
        const $rows = $inlineGroup.find('tr.form-row:not(.add-row)');
        let hasErrors = false;
        
        // Проверяем, что есть хотя бы одно изображение
        let hasImages = false;
        $rows.each(function() {
            const $row = $(this);
            const $fileInput = $row.find('input[type="file"]');
            const $deleteCheckbox = $row.find('input[name$="-DELETE"]');
            
            if (($fileInput.val() || $row.find('.image-preview img').attr('src')) && !$deleteCheckbox.is(':checked')) {
                hasImages = true;
            }
        });
        
        if (!hasImages) {
            alert('Необходимо добавить хотя бы одно изображение.');
            hasErrors = true;
        }
        
        return !hasErrors;
    }

    // Привязываем валидацию к отправке формы
    $(document).on('submit', '#background_content_form', function(e) {
        if (!validateForms()) {
            e.preventDefault();
            return false;
        }
    });

})(django.jQuery || jQuery || $);