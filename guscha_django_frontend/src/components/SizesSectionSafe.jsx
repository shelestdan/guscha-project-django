import React from 'react';

// Безопасная версия компонента размеров без внешних зависимостей
const SizesSectionSafe = ({ 
  formData, 
  handleSizeChange, 
  addSize, 
  removeSize, 
  saving 
}) => {
  // Проверяем, что все пропсы переданы корректно
  if (!formData || !formData.sizes || !Array.isArray(formData.sizes)) {
    console.error('SizesSectionSafe: Invalid formData or sizes array');
    return <div>Ошибка загрузки размеров</div>;
  }

  if (typeof handleSizeChange !== 'function') {
    console.error('SizesSectionSafe: handleSizeChange is not a function');
    return <div>Ошибка: handleSizeChange не является функцией</div>;
  }

  return (
    <div className="sizes-section-safe">
      <div className="sizes-header">
        <h3>Размеры и управление наличием</h3>
        <button 
          type="button" 
          className="btn btn-secondary" 
          onClick={addSize}
          disabled={saving}
        >
          + Добавить размер
        </button>
      </div>
      
      <div className="sizes-table-improved">
        <div className="sizes-table-header-improved">
          <div className="header-cell-improved">Размер</div>
          <div className="header-cell-improved">Количество</div>
          <div className="header-cell-improved">Ограничения</div>
          <div className="header-cell-improved">Нет в наличии</div>
          <div className="header-cell-improved">Активен</div>
          <div className="header-cell-improved">Действия</div>
        </div>
        
        <div className="sizes-table-body-improved">
          {formData.sizes.map((size, index) => (
            <div key={index} className="size-row-improved">
              <div className="size-cell-improved">
                <label className="cell-label-improved">Размер</label>
                <input
                  type="text"
                  placeholder="S, M, L, XL"
                  value={size.size_name || ''}
                  onChange={(e) => handleSizeChange(index, 'size_name', e.target.value)}
                  disabled={saving}
                  className="size-input-improved"
                />
              </div>
              
              <div className="size-cell-improved">
                <label className="cell-label-improved">Количество</label>
                <input
                  type="number"
                  placeholder="0"
                  min="0"
                  value={size.stock_quantity || 0}
                  onChange={(e) => handleSizeChange(index, 'stock_quantity', parseInt(e.target.value) || 0)}
                  disabled={saving}
                  className="quantity-input-improved"
                />
              </div>
              
              <div className="size-cell-improved">
                <label className="cell-label-improved">Ограничения</label>
                <input
                  type="number"
                  placeholder="Без ограничений"
                  min="1"
                  value={size.max_quantity || ''}
                  onChange={(e) => handleSizeChange(index, 'max_quantity', e.target.value ? parseInt(e.target.value) : null)}
                  disabled={saving}
                  className="limit-input-improved"
                  title="Максимальное количество для заказа (пустое = без ограничений)"
                />
              </div>
              
              <div className="size-cell-improved checkbox-cell-improved">
                <label className="cell-label-improved">Нет в наличии</label>
                <label className="checkbox-container-improved">
                  <input
                    type="checkbox"
                    checked={size.is_sold_out || false}
                    onChange={(e) => handleSizeChange(index, 'is_sold_out', e.target.checked)}
                    disabled={saving}
                    title="Размер отсутствует в наличии"
                  />
                  <span className="checkmark-improved"></span>
                </label>
              </div>
              
              <div className="size-cell-improved checkbox-cell-improved">
                <label className="cell-label-improved">Активен</label>
                <label className="checkbox-container-improved">
                  <input
                    type="checkbox"
                    checked={size.is_active !== false}
                    onChange={(e) => handleSizeChange(index, 'is_active', e.target.checked)}
                    disabled={saving}
                    title="Размер активен"
                  />
                  <span className="checkmark-improved"></span>
                </label>
              </div>
              
              <div className="size-cell-improved action-cell-improved">
                <label className="cell-label-improved">Действия</label>
                <button 
                  type="button" 
                  className="btn-icon-improved delete-improved"
                  onClick={() => removeSize(index)}
                  disabled={saving}
                  title="Удалить размер"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="sizes-help-improved">
        <div className="help-item-improved">
          <strong>Нет в наличии:</strong> Размер отображается, но его нельзя выбрать
        </div>
        <div className="help-item-improved">
          <strong>Активен:</strong> Размер отображается и доступен для выбора
        </div>
        <div className="help-item-improved">
          <strong>Ограничения:</strong> Максимальное количество для добавления в корзину
        </div>
      </div>
    </div>
  );
};

export default SizesSectionSafe;