/*
 * Кастомный JavaScript для Django admin inline formsets
 * Обеспечивает правильное позиционирование кнопки "Добавить еще" в конце списка
 */

(function() {
    'use strict';

    // Ждем загрузки jQuery и Django admin
    function initCustomInlines() {
        var $ = window.jQuery || window.django.jQuery;
        if (!$ || !$.fn.formset) {
            setTimeout(initCustomInlines, 100);
            return;
        }

        // Функция для управления кнопками "Добавить еще" - удаляет дубликаты и оставляет одну в конце
        function moveAddButtonToEnd(formsetPrefix) {
            var $formset = $('#' + formsetPrefix + '-group');
            var $table = $formset.find('table');
            var $tbody = $table.find('tbody');
            var $addButtonRows = $tbody.find('tr.add-row');
            
            if ($addButtonRows.length && $tbody.length) {
                // Если есть несколько кнопок "Добавить еще", удаляем все кроме последней
                if ($addButtonRows.length > 1) {
                    $addButtonRows.slice(0, -1).remove();
                    $addButtonRows = $tbody.find('tr.add-row'); // Обновляем селектор
                }
                
                // Проверяем, не находится ли кнопка уже в конце
                var $lastRow = $tbody.children('tr').last();
                if (!$lastRow.hasClass('add-row') && $addButtonRows.length > 0) {
                    // Перемещаем строку с кнопкой "Добавить еще" в самый конец tbody
                    $addButtonRows.detach();
                    $tbody.append($addButtonRows);
                }
            }
        }

        // Сохраняем оригинальную функцию formset
        var originalFormset = $.fn.formset;
        
        // Переопределяем функцию formset
        $.fn.formset = function(opts) {
            var options = $.extend({}, $.fn.formset.defaults, opts);
            var $this = $(this);
            var prefix = $this.attr('id').replace('-group', '');
            
            // Сохраняем оригинальный callback
            var originalAddedCallback = options.added;
            
            // Добавляем наш обработчик
            options.added = function(row) {
                if (originalAddedCallback) {
                    originalAddedCallback(row);
                }
                // Перемещаем кнопку "Добавить еще" в конец после добавления новой строки
                setTimeout(function() {
                    moveAddButtonToEnd(prefix);
                }, 50);
            };
            
            // Вызываем оригинальную функцию с нашими опциями
            return originalFormset.call(this, options);
        };
        
        // Копируем defaults из оригинальной функции
        $.fn.formset.defaults = originalFormset.defaults;

        // Инициализация при загрузке страницы
        $(document).ready(function() {
            // Находим все inline группы и перемещаем кнопки "Добавить еще" в конец
            function initializeAddButtons() {
                $('.inline-group').each(function() {
                    var $group = $(this);
                    var groupId = $group.attr('id');
                    
                    if (groupId && groupId.endsWith('-group')) {
                        var prefix = groupId.replace('-group', '');
                        moveAddButtonToEnd(prefix);
                    }
                });
            }
            
            // Первоначальная инициализация с задержкой для полной загрузки DOM
            setTimeout(function() {
                initializeAddButtons();
            }, 100);
            
            // Обработчик для кнопок добавления
            $(document).on('click', '.add-row a', function() {
                var $group = $(this).closest('.inline-group');
                var groupId = $group.attr('id');
                if (groupId && groupId.endsWith('-group')) {
                    var prefix = groupId.replace('-group', '');
                    setTimeout(function() {
                        moveAddButtonToEnd(prefix);
                    }, 100);
                }
            });
            
            // Обработчик для кнопок удаления
            $(document).on('click', '.delete-row', function() {
                var $group = $(this).closest('.inline-group');
                var groupId = $group.attr('id');
                if (groupId && groupId.endsWith('-group')) {
                    var prefix = groupId.replace('-group', '');
                    setTimeout(function() {
                        moveAddButtonToEnd(prefix);
                    }, 100);
                }
            });
        });
    }

    // Запускаем инициализацию
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCustomInlines);
    } else {
        initCustomInlines();
    }

})();