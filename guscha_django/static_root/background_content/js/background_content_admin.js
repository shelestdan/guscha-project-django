// JavaScript для динамического показа/скрытия полей в админ-панели background_content

(function ($) {
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
        switch (contentType) {
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
        $('.inline-group').each(function () {
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
        $('fieldset').each(function () {
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
        $('.inline-group').each(function () {
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

    // Функция для обработки инлайнов видео (плейлист)
    function handleVideoItemInlines() {
        // Helper to setup a single row
        function setupRow($row) {
            var $platformSelect = $row.find('select[name$="-platform"]');
            var $urlInput = $row.find('input[name$="-video_url"]');
            var $fileInput = $row.find('input[type="file"][name$="-file"]');

            // Если элементов нет (например, другая вкладка), выходим
            if (!$platformSelect.length) return;

            function updateVisibility() {
                var platform = $platformSelect.val();
                if (platform === 'file') {
                    $urlInput.hide();
                    $fileInput.closest('.field-file').show();
                    // Также скроем ошибку если есть (визуально)
                } else {
                    $urlInput.show();
                    // Не скрываем полностью файл, вдруг пользователь хочет заменить его? 
                    // Но для ясности можно приглушить.
                    // $fileInput.closest('.field-file').hide(); 
                    // Лучше оставить, но фокус на URL
                }
            }

            // 1. При выборе файла АВТОМАТИЧЕСКИ переключаем на 'file'
            $fileInput.on('change', function () {
                if ($(this).val()) {
                    $platformSelect.val('file').trigger('change');
                }
            });

            // Если есть уже загруженный файл (ссылка в DOM), и платформа youtube/vimeo - переключаем на file
            // Это исправляет ситуацию при перезагрузке страницы с ошибкой
            var $currFileLink = $row.find('.file-upload a, .field-file a');
            if ($currFileLink.length && $platformSelect.val() !== 'file') {
                // Только если поле URL пустое (чтобы не ломать если пользователь хочет сменить на URL)
                if (!$urlInput.val()) {
                    $platformSelect.val('file').trigger('change');
                }
            }

            // 2. При вводе URL можно переключать на YouTube (опционально, но удобно)
            $urlInput.on('input', function () {
                var val = $(this).val();
                if (val && $platformSelect.val() === 'file') {
                    // Если начали писать URL, а стоял файл -> меняем на ютуб
                    if (val.includes('vimeo')) {
                        $platformSelect.val('vimeo').trigger('change');
                    } else {
                        $platformSelect.val('youtube').trigger('change');
                    }
                }
            });

            // 3. Обработка смены платформы
            $platformSelect.on('change', updateVisibility);

            // Инициализация
            updateVisibility();
        }

        // Применяем к существующим строкам
        $('.dynamic-video_items').each(function () {
            setupRow($(this));
        });

        // Слушаем добавление новых строк
        $(document).on('formset:added', function (event, $row) {
            if ($row.hasClass('dynamic-video_items')) {
                setupRow($row);
            }
        });
    }

    // Функция для предварительного просмотра изображений
    function setupImagePreview() {
        $('input[type="file"][accept*="image"]').on('change', function () {
            var file = this.files[0];
            var $preview = $(this).siblings('.image-preview');

            if (!$preview.length) {
                $preview = $('<img class="image-preview" alt="Предварительный просмотр">');
                $(this).after($preview);
            }

            if (file) {
                var reader = new FileReader();
                reader.onload = function (e) {
                    $preview.attr('src', e.target.result).show();
                };
                reader.readAsDataURL(file);
            } else {
                $preview.hide();
            }
        });
    }

    // Функция проверки формы перед отправкой
    function setupValidation() {
        $('form').on('submit', function (e) {
            // Client-side validation handled by backend
        });
    }

    // Инициализация при загрузке DOM
    $(document).ready(function () {
        // Добавляем классы к полям
        addFieldClasses();

        // Настраиваем обработчики
        $('#id_content_type').on('change', toggleContentFields);

        // Инициализируем показ полей
        toggleContentFields();


        // Настраиваем поля видео
        handleVideoItemInlines();

        // Настраиваем предварительный просмотр изображений
        setupImagePreview();

        // Настраиваем валидацию
        setupValidation();

        // Обработка динамически добавляемых inline форм
        $(document).on('formset:added', function (event, $row) {
            // Переинициализируем для новых строк
            addFieldClasses();
            setupImagePreview();
        });
    });

    // Совместимость с Django Unfold
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).ready(function () {
            // Дублируем инициализацию для Django Unfold
            addFieldClasses();
            $('#id_content_type').on('change', toggleContentFields);
            toggleContentFields();
            handleVideoItemInlines();
            setupImagePreview();
            setupValidation();
        });
    }

})(django.jQuery || jQuery || $);

// Дополнительная инициализация для случаев, когда jQuery загружается позже
if (typeof $ === 'undefined') {
    document.addEventListener('DOMContentLoaded', function () {
        if (typeof $ !== 'undefined') {
            // Повторная инициализация, если jQuery стал доступен
            $(document).ready(function () {
                addFieldClasses();
                $('#id_content_type').on('change', toggleContentFields);
                toggleContentFields();
                handleVideoItemInlines();
                setupImagePreview();
                setupValidation();
            });
        }
    });
}