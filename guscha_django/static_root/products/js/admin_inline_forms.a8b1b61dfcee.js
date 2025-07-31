/**
 * Улучшение интерфейса inline форм в Django админке
 * Создает кастомную кнопку для добавления размеров товаров
 */

(function($) {
    'use strict';

    // Хранилище для функций добавления форм
    let addFormFunctions = new Map();
    
    // Функция для поиска inline групп в разных структурах админки
    function findInlineGroups() {
        const selectors = [
            '.inline-group',
            '.inline-related',
            '[class*="inline"]',
            '.tabular',
            '.stacked'
        ];
        
        let $groups = $();
        selectors.forEach(selector => {
            $groups = $groups.add($(selector));
        });
        
        return $groups.filter(function() {
            const $this = $(this);
            return $this.find('table').length > 0 || 
                   $this.find('[name*="size"]').length > 0 ||
                   $this.find('h2, h3, .inline-title').text().toLowerCase().includes('размер');
        });
    }

    // Функция для сохранения оригинальных функций добавления
    function saveOriginalAddFunctions() {
        console.log('Поиск inline групп...');
        const $inlineGroups = findInlineGroups();
        console.log('Найдено inline групп:', $inlineGroups.length);
        
        $inlineGroups.each(function() {
            const $inlineGroup = $(this);
            console.log('Обрабатываем группу:', $inlineGroup[0]);
            
            // Ищем кнопки добавления в разных местах
            const $addLinks = $inlineGroup.find('.add-row a, .addlink, a[href*="__prefix__"], button[onclick*="add"]');
            console.log('Найдено кнопок добавления:', $addLinks.length);
            
            if ($addLinks.length > 0) {
                const groupId = $inlineGroup.attr('id') || 
                               $inlineGroup.find('table').attr('id') || 
                               $inlineGroup.attr('class') + '-' + Math.random();
                
                console.log('ID группы:', groupId);
                
                const $addLink = $addLinks.first();
                
                // Сохраняем оригинальную функцию onclick
                const originalOnClick = $addLink[0].onclick;
                if (originalOnClick) {
                    console.log('Сохраняем onclick функцию для:', groupId);
                    addFormFunctions.set(groupId, originalOnClick);
                } else {
                    // Если onclick не установлен, создаем функцию на основе href
                    const href = $addLink.attr('href');
                    console.log('href кнопки:', href);
                    
                    if (href && href.includes('__prefix__')) {
                        console.log('Создаем функцию добавления для:', groupId);
                        addFormFunctions.set(groupId, function() {
                            console.log('Выполняем добавление формы...');
                            // Используем стандартный механизм Django для добавления форм
                            const totalForms = $inlineGroup.find('input[name$="-TOTAL_FORMS"]');
                            if (totalForms.length > 0) {
                                const currentTotal = parseInt(totalForms.val());
                                console.log('Текущее количество форм:', currentTotal);
                                
                                // Симулируем клик по оригинальной кнопке
                                $addLink[0].click();
                                
                                // Диспетчим событие для совместимости
                                const event = new CustomEvent('formset:added', {
                                    detail: {
                                        formsetName: groupId,
                                        totalForms: currentTotal + 1
                                    }
                                });
                                document.dispatchEvent(event);
                            }
                        });
                    }
                }
                
                // Сохраняем ID группы как атрибут
                $inlineGroup.attr('data-group-id', groupId);
            }
        });
    }

    // Функция для создания кастомных кнопок
    function createCustomButtons() {
        console.log('Создание кастомных кнопок...');
        const $inlineGroups = findInlineGroups();
        console.log('Найдено групп для кнопок:', $inlineGroups.length);
        
        $inlineGroups.each(function() {
            const $inlineGroup = $(this);
            const $table = $inlineGroup.find('table');
            const groupId = $inlineGroup.attr('data-group-id') || 
                           $inlineGroup.attr('id') || 
                           $inlineGroup.find('table').attr('id') || 
                           $inlineGroup.attr('class') + '-' + Math.random();
            
            console.log('Обрабатываем группу для кнопки:', groupId);
            
            // Проверяем, что это группа размеров или изображений (по заголовку или классу)
            const $headers = $inlineGroup.find('h2, h3, .inline-title, legend');
            const headerText = $headers.text().toLowerCase();
            const isProductSize = headerText.includes('размер') || 
                                headerText.includes('size') ||
                                $inlineGroup.find('[name*="productsize"]').length > 0 ||
                                $inlineGroup.find('[name*="preordersize"]').length > 0 ||
                                $inlineGroup.find('[name*="size"]').length > 0;
            
            const isProductImage = headerText.includes('изображени') ||
                                 headerText.includes('image') ||
                                 $inlineGroup.find('[name*="productimage"]').length > 0 ||
                                 $inlineGroup.find('[name*="preorderimage"]').length > 0 ||
                                 $inlineGroup.find('[name*="image"]').length > 0;
            
            console.log('Это группа размеров?', isProductSize);
            console.log('Это группа изображений?', isProductImage);
            console.log('Есть функция добавления?', addFormFunctions.has(groupId));
            
            if ($table.length && (isProductSize || isProductImage)) {
                // Удаляем существующий контейнер кнопки, если есть
                $inlineGroup.find('.add-button-container').remove();
                
                // Создаем контейнер для кнопки
                const $buttonContainer = $('<div class="add-button-container" style="text-align: right; margin: 10px 0; padding: 10px;"></div>');
                
                // Создаем кнопку в стиле админки
                const buttonText = isProductSize ? '+ Добавить размер' : '+ Добавить изображение';
                const $button = $('<button type="button" class="bg-primary-600 border border-transparent cursor-pointer font-medium px-3 py-2 rounded-default text-white hover:bg-primary-700 transition-colors" style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border-radius: 6px; padding: 8px 16px; font-weight: 500;">' + buttonText + '</button>');
                
                // Добавляем обработчик клика
                $button.on('click', function(e) {
                    e.preventDefault();
                    console.log('Клик по кнопке добавления');
                    
                    // Ищем оригинальную кнопку добавления
                    const $originalButton = $inlineGroup.find('.add-row a, .addlink, a[href*="__prefix__"]').first();
                    if ($originalButton.length > 0) {
                        console.log('Кликаем по оригинальной кнопке');
                        $originalButton[0].click();
                    } else {
                        console.log('Используем сохраненную функцию');
                        const addFunction = addFormFunctions.get(groupId);
                        if (addFunction) {
                            try {
                                addFunction.call(this);
                            } catch (error) {
                                console.error('Ошибка при добавлении формы:', error);
                            }
                        }
                    }
                });
                
                $buttonContainer.append($button);
                $table.after($buttonContainer);
                console.log('Кнопка добавлена для группы:', groupId);
            }
        });
    }

    // Функция для скрытия стандартных элементов
    function hideStandardElements() {
        // Скрываем стандартные кнопки добавления
        $('tr.add-row, a.addlink, div.add-row').hide();
    }

    // Основная функция инициализации
    function initializeCustomButtons() {
        saveOriginalAddFunctions();
        createCustomButtons();
        hideStandardElements();
    }

    // Инициализация при загрузке страницы
    $(document).ready(function() {
        initializeCustomButtons();
        
        // Наблюдаем за изменениями в DOM для новых inline форм
        const observer = new MutationObserver(function(mutations) {
            let shouldReinitialize = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) {
                            const $node = $(node);
                            // Проверяем, добавлены ли новые inline группы или формы
                            if ($node.hasClass('inline-group') || 
                                $node.find('.inline-group').length > 0 ||
                                $node.hasClass('add-row') || 
                                $node.hasClass('addlink') || 
                                $node.find('.add-row, .addlink').length > 0) {
                                shouldReinitialize = true;
                            }
                        }
                    });
                }
            });
            
            if (shouldReinitialize) {
                // Небольшая задержка для завершения DOM операций
                setTimeout(initializeCustomButtons, 100);
            }
        });
        
        // Начинаем наблюдение
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Слушаем события Django formset для совместимости
        document.addEventListener('formset:added', function(e) {
            setTimeout(function() {
                hideStandardElements();
                createCustomButtons();
            }, 50);
        });
        
        document.addEventListener('formset:removed', function(e) {
            setTimeout(function() {
                hideStandardElements();
                createCustomButtons();
            }, 50);
        });
    });

})(django.jQuery || jQuery);