/**
 * Улучшение интерфейса inline форм в Django админке
 * Удаляет стандартные элементы и создает кнопку в стиле админки
 */

(function($) {
    'use strict';

    // Функция для удаления ненужных элементов и создания новой кнопки
    function replaceAddElements() {
        // Удаляем все tr.add-row элементы
        $('tr.add-row').remove();
        
        // Удаляем все a.addlink элементы
        $('a.addlink').remove();
        
        // Удаляем все div.add-row элементы
        $('div.add-row').remove();
        
        // Находим inline группы и добавляем кнопку
        $('.inline-group').each(function() {
            const $inlineGroup = $(this);
            const $table = $inlineGroup.find('table');
            
            if ($table.length) {
                // Создаем контейнер для кнопки справа
                const $buttonContainer = $('<div class="add-button-container" style="text-align: right; margin: 10px 0; padding: 10px;"></div>');
                
                // Создаем кнопку в стиле админки
                const $button = $('<button type="button" class="bg-primary-600 border border-transparent cursor-pointer font-medium px-3 py-2 rounded-default text-white">+ Добавить ещё</button>');
                
                // Добавляем обработчик клика
                $button.on('click', function() {
                    // Находим последнюю форму в inline группе
                    const $forms = $inlineGroup.find('.dynamic-form');
                    if ($forms.length > 0) {
                        // Эмулируем клик по кнопке добавления Django
                        const addButton = $inlineGroup.find('.add-row a')[0];
                        if (addButton && addButton.click) {
                            addButton.click();
                        }
                    }
                });
                
                $buttonContainer.append($button);
                $table.after($buttonContainer);
            }
        });
    }

    // Инициализация при загрузке страницы
    $(document).ready(function() {
        // Заменяем элементы
        replaceAddElements();
        
        // Наблюдаем за изменениями в DOM для новых inline форм
        const observer = new MutationObserver(function(mutations) {
            let shouldUpdate = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && 
                            (node.classList.contains('add-row') || 
                             node.querySelector && (node.querySelector('.add-row') || node.querySelector('.addlink')))) {
                            shouldUpdate = true;
                        }
                    });
                }
            });
            
            if (shouldUpdate) {
                setTimeout(function() {
                    replaceAddElements();
                }, 100);
            }
        });
        
        // Начинаем наблюдение за изменениями в области inline форм
        const inlineGroups = document.querySelectorAll('.inline-group');
        inlineGroups.forEach(function(group) {
            observer.observe(group, {
                childList: true,
                subtree: true
            });
        });
        
        // Также наблюдаем за всем документом для новых элементов
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });

})(django.jQuery || jQuery);