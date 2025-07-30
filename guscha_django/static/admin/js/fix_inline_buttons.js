/**
 * Исправляет отображение кнопок добавления в inline формах Django Unfold
 */
document.addEventListener('DOMContentLoaded', function() {
    // Функция для проверки и исправления кнопок
    function fixInlineButtons() {
        // Проверяем Unfold специфичные табличные inline формы
        const tabularInlines = document.querySelectorAll('.tabular.inline-related');
        
        tabularInlines.forEach(function(inline) {
            const parentContainer = inline.closest('.inline-group');
            if (!parentContainer) return;
            
            // Проверяем наличие кнопки добавления
            let addButton = parentContainer.querySelector('.add-row a, .addlink');
            
            if (!addButton) {
                // Создаем контейнер для кнопки в стиле Unfold
                const addRowDiv = document.createElement('div');
                addRowDiv.className = 'add-row';
                addRowDiv.style.cssText = 'margin-top: 12px; padding: 8px 0;';
                
                // Создаем кнопку в стиле Unfold
                const addLink = document.createElement('a');
                addLink.href = '#';
                addLink.className = 'addlink';
                addLink.style.cssText = 'display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: var(--primary-500, #a855f7); color: white; border-radius: 6px; text-decoration: none; font-weight: 500; transition: all 0.2s;';
                
                // Добавляем иконку и текст
                addLink.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg><span>Добавить ещё</span>';
                
                // Обработчик клика
                addLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    
                    // Используем Django jQuery для добавления формы
                    if (window.django && window.django.jQuery) {
                        const $ = window.django.jQuery;
                        
                        // Находим formset контейнер
                        const formsetContainer = parentContainer.querySelector('.js-inline-admin-formset');
                        if (formsetContainer) {
                            const $formset = $(formsetContainer);
                            const prefix = $formset.data('inline-formset') || $formset.attr('id').replace('-group', '');
                            
                            // Находим все существующие формы
                            const $forms = $formset.find('.form-row:not(.empty-form)');
                            
                            if ($forms.length > 0) {
                                // Клонируем последнюю форму
                                const $lastForm = $forms.last();
                                const $newForm = $lastForm.clone(true);
                                
                                // Получаем текущий индекс
                                const totalFormsInput = parentContainer.querySelector('input[name$="-TOTAL_FORMS"]');
                                if (totalFormsInput) {
                                    const currentTotal = parseInt(totalFormsInput.value);
                                    
                                    // Обновляем все поля в новой форме
                                    $newForm.find('input, select, textarea').each(function() {
                                        const $field = $(this);
                                        const name = $field.attr('name');
                                        const id = $field.attr('id');
                                        
                                        if (name) {
                                            // Заменяем индекс в name
                                            const newName = name.replace(/-\d+-/, '-' + currentTotal + '-');
                                            $field.attr('name', newName);
                                        }
                                        
                                        if (id) {
                                            // Заменяем индекс в id
                                            const newId = id.replace(/-\d+-/, '-' + currentTotal + '-');
                                            $field.attr('id', newId);
                                        }
                                        
                                        // Очищаем значения
                                        if ($field.attr('type') !== 'hidden' || $field.attr('name').includes('DELETE')) {
                                            $field.val('');
                                        }
                                        
                                        // Снимаем отметку DELETE
                                        if ($field.attr('name') && $field.attr('name').includes('DELETE')) {
                                            $field.prop('checked', false);
                                        }
                                    });
                                    
                                    // Обновляем labels
                                    $newForm.find('label').each(function() {
                                        const $label = $(this);
                                        const forAttr = $label.attr('for');
                                        if (forAttr) {
                                            const newFor = forAttr.replace(/-\d+-/, '-' + currentTotal + '-');
                                            $label.attr('for', newFor);
                                        }
                                    });
                                    
                                    // Вставляем новую форму
                                    $lastForm.after($newForm);
                                    
                                    // Обновляем TOTAL_FORMS
                                    totalFormsInput.value = currentTotal + 1;
                                    
                                    // Инициализируем новые поля
                                    if (window.initPrepopulatedFields) {
                                        window.initPrepopulatedFields($newForm);
                                    }
                                    
                                    console.log('Добавлена новая inline форма с индексом:', currentTotal);
                                }
                            }
                        }
                    }
                });
                
                // Эффект при наведении
                addLink.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = 'var(--primary-600, #9333ea)';
                    this.style.transform = 'translateY(-1px)';
                    this.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
                });
                
                addLink.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = 'var(--primary-500, #a855f7)';
                    this.style.transform = 'translateY(0)';
                    this.style.boxShadow = 'none';
                });
                
                addRowDiv.appendChild(addLink);
                
                // Вставляем после табличной формы
                inline.parentNode.insertBefore(addRowDiv, inline.nextSibling);
            }
        });
        
        // Проверяем Unfold специфичные элементы
        const unfoldInlines = document.querySelectorAll('[data-inline-type="tabular"]');
        unfoldInlines.forEach(function(inline) {
            const addButton = inline.querySelector('.add-inline-link, .add-row-link');
            if (!addButton) {
                console.log('Unfold inline без кнопки добавления найден:', inline);
                
                // Пытаемся найти контейнер для кнопок
                const actionsContainer = inline.querySelector('.inline-related-actions, .inline-actions');
                if (actionsContainer) {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'button button--primary add-inline-link';
                    button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg> Добавить';
                    
                    button.addEventListener('click', function(e) {
                        e.preventDefault();
                        // Эмулируем клик на скрытую кнопку или вызываем функцию добавления
                        const hiddenAddButton = inline.querySelector('a.add-row');
                        if (hiddenAddButton) {
                            hiddenAddButton.click();
                        }
                    });
                    
                    actionsContainer.appendChild(button);
                }
            }
        });
    }
    
    // Запускаем исправление при загрузке
    fixInlineButtons();
    
    // Также запускаем после изменений в DOM (для динамически загружаемого контента)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                fixInlineButtons();
            }
        });
    });
    
    // Наблюдаем за изменениями в основном контенте админки
    const adminContent = document.querySelector('.main, #content, .content');
    if (adminContent) {
        observer.observe(adminContent, { childList: true, subtree: true });
    }
    
    // Дополнительная проверка для табов
    document.addEventListener('click', function(e) {
        if (e.target.matches('.tab-link, [role="tab"]')) {
            setTimeout(fixInlineButtons, 100);
        }
    });
});

// Дополнительное исправление для Unfold
if (window.Unfold) {
    const originalInit = window.Unfold.init;
    window.Unfold.init = function() {
        if (originalInit) {
            originalInit.apply(this, arguments);
        }
        setTimeout(function() {
            document.dispatchEvent(new Event('DOMContentLoaded'));
        }, 100);
    };
}
