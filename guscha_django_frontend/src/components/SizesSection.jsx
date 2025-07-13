import React from 'react';
import { FiPlus, FiTrash2 } from 'react-icons/fi';

const SizesSection = ({ 
  formData, 
  handleSizeChange, 
  addSize, 
  removeSize, 
  saving 
}) => {
  return (
    <div className="sizes-section">
      <div className="sizes-header">
        <h3>Размеры и управление наличием</h3>
        <button 
          type="button" 
          className="btn btn-secondary" 
          onClick={addSize}
          disabled={saving}
        >
          <FiPlus /> Добавить размер
        </button>
      </div>
      
      <div className="sizes-table">
        <div className="sizes-table-header">
          <div className="header-cell">Размер</div>
          <div className="header-cell">Количество</div>
          <div className="header-cell">Ограничения</div>
          <div className="header-cell">Нет в наличии</div>
          <div className="header-cell">Активен</div>
          <div className="header-cell">Действия</div>
        </div>
        
        <div className="sizes-table-body">
          {formData.sizes.map((size, index) => (
            <div key={index} className="size-row">
              <div className="size-cell">
                <label className="cell-label">Размер</label>
                <input
                  type="text"
                  placeholder="S, M, L, XL"
                  value={size.size_name}
                  onChange={(e) => handleSizeChange(index, 'size_name', e.target.value)}
                  disabled={saving}
                  className="size-input"
                />
              </div>
              
              <div className="size-cell">
                <label className="cell-label">Количество</label>
                <input
                  type="number"
                  placeholder="0"
                  min="0"
                  value={size.stock_quantity}
                  onChange={(e) => handleSizeChange(index, 'stock_quantity', parseInt(e.target.value) || 0)}
                  disabled={saving}
                  className="quantity-input"
                />
              </div>
              
              <div className="size-cell">
                <label className="cell-label">Ограничения</label>
                <input
                  type="number"
                  placeholder="Без ограничений"
                  min="0"
                  value={size.max_quantity || ''}
                  onChange={(e) => handleSizeChange(index, 'max_quantity', e.target.value ? parseInt(e.target.value) : null)}
                  disabled={saving}
                  className="limit-input"
                  title="Максимальное количество для заказа (пустое = без ограничений)"
                />
              </div>
              
              <div className="size-cell checkbox-cell">
                <label className="cell-label">Нет в наличии</label>
                <label className="checkbox-container">
                  <input
                    type="checkbox"
                    checked={size.is_sold_out}
                    onChange={(e) => handleSizeChange(index, 'is_sold_out', e.target.checked)}
                    disabled={saving}
                    title="Размер отсутствует в наличии (отображается, но нельзя выбрать)"
                  />
                  <span className="checkmark"></span>
                </label>
              </div>
              
              <div className="size-cell checkbox-cell">
                <label className="cell-label">Активен</label>
                <label className="checkbox-container">
                  <input
                    type="checkbox"
                    checked={size.is_active}
                    onChange={(e) => handleSizeChange(index, 'is_active', e.target.checked)}
                    disabled={saving}
                    title="Размер активен (отображается на странице товара)"
                  />
                  <span className="checkmark"></span>
                </label>
              </div>
              
              <div className="size-cell action-cell">
                <label className="cell-label">Действия</label>
                <button 
                  type="button" 
                  className="btn-icon delete"
                  onClick={() => removeSize(index)}
                  disabled={saving}
                  title="Удалить размер"
                >
                  <FiTrash2 />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="sizes-help">
        <div className="help-item">
          <strong>Нет в наличии:</strong> Размер отображается на странице товара, но его нельзя выбрать (закончился)
        </div>
        <div className="help-item">
          <strong>Активен:</strong> Размер отображается на странице товара и доступен для выбора
        </div>
        <div className="help-item">
          <strong>Ограничения:</strong> Максимальное количество данного размера, которое можно добавить в корзину за один раз
        </div>
      </div>
    </div>
  );
};

export default SizesSection;