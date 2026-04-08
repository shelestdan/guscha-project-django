import React, { useState, useEffect } from 'react';
import { FiPlus, FiTrash2, FiX } from 'react-icons/fi';
import SizesSection from './SizesSection';
import '../styles/SizesSection.css';
import axios from '../api/axiosInstance';

const ProductFormEnhanced = ({ product, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: product?.name || '',
    description: product?.description || '',
    price: product?.price || '',
    sku: product?.sku || '',
    category_id: product?.category_id || null,
    image_url: product?.image_url || '',
    images: (() => {
      const additionalImages = product?.additional_images || product?.images || [];
      const parsedImages = Array.isArray(additionalImages) 
        ? additionalImages 
        : (typeof additionalImages === 'string' ? JSON.parse(additionalImages) : []);
      return parsedImages.filter(img => img && img !== product?.image_url);
    })(),
    is_active: product?.is_active ?? true,
    sizes: product?.sizes?.map(size => ({
      id: size.id,
      size_name: size.size_name || size.size || '',
      stock_quantity: size.stock_quantity || size.quantity || 0,
      max_quantity: size.max_quantity || null,
      is_active: size.is_active ?? true,
      is_sold_out: size.is_sold_out ?? false
    })) || [{ size_name: '', stock_quantity: 0, max_quantity: null, is_active: true, is_sold_out: false }]
  });
  
  const [categories, setCategories] = useState([]);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get('/api/admin/categories');
        setCategories(response.data);
      } catch (error) {
        // Ошибка загрузки категорий не критична для формы, просто оставляем пустой список
      }
    };

    fetchCategories();
  }, []);

  const showNotification = (type, title, message) => {
    setNotification({ type, title, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      const url = product 
        ? `/api/admin/products/${product.id}`
        : '/api/admin/products';
      
      const submitData = {
        name: formData.name,
        description: formData.description,
        price: parseFloat(formData.price),
        category_id: formData.category_id,
        is_active: formData.is_active,
        sku: formData.sku || '',
        sizes: formData.sizes.filter(size => size.size_name.trim() !== '').map(size => ({
          id: size.id || undefined,
          size_name: size.size_name,
          stock_quantity: parseInt(size.stock_quantity) || 0,
          max_quantity: size.max_quantity ? parseInt(size.max_quantity) : null,
          is_active: size.is_active,
          is_sold_out: size.is_sold_out
        }))
      };

      if (formData.image_url && formData.image_url.trim() !== '') {
        submitData.image_url = formData.image_url;
      }

      if (formData.images && formData.images.length > 0) {
        submitData.additional_images = formData.images.filter(img => img && img.trim() !== '');
      }

      let response;
      if (product) {
        response = await axios.put(url, submitData);
      } else {
        response = await axios.post(url, submitData);
      }

      if (response.data && response.data.product) {
        showNotification(
          'success',
          'Успешно!',
          product ? 'Товар успешно обновлен' : 'Товар успешно создан'
        );
        
        setTimeout(() => {
          onSave();
        }, 1000);
      } else {
        throw new Error('Сервер не вернул данные товара');
      }
    } catch (error) {
      let errorMessage = 'Произошла ошибка при сохранении';
      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response?.data?.errors) {
        errorMessage = Object.values(error.response.data.errors).flat().join(', ');
      }
      
      showNotification('error', 'Ошибка', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleSizeChange = (index, field, value) => {
    const newSizes = [...formData.sizes];
    newSizes[index][field] = value;
    setFormData({ ...formData, sizes: newSizes });
  };

  const addSize = () => {
    setFormData({
      ...formData,
      sizes: [...formData.sizes, { 
        size_name: '', 
        stock_quantity: 0, 
        max_quantity: null, 
        is_active: true, 
        is_sold_out: false 
      }]
    });
  };

  const removeSize = (index) => {
    const newSizes = formData.sizes.filter((_, i) => i !== index);
    setFormData({ ...formData, sizes: newSizes });
  };

  return (
    <>
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-header">
            <h2>{product ? 'Редактировать товар' : 'Добавить товар'}</h2>
            <button className="modal-close" onClick={onCancel}>×</button>
          </div>
          
          <form className="product-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Название товара</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  disabled={saving}
                />
              </div>
              
              <div className="form-group">
                <label>Цена</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  required
                  disabled={saving}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>SKU (артикул)</label>
                <input
                  type="text"
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  placeholder="Введите SKU (необязательно)"
                  disabled={saving}
                />
              </div>
              
              <div className="form-group">
                <label>Категория</label>
                <select
                  value={formData.category_id || ''}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value ? parseInt(e.target.value) : null })}
                  disabled={saving}
                >
                  <option value="">Выберите категорию (необязательно)</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Описание</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                disabled={saving}
              />
            </div>

            <div className="form-group">
              <label>Основное изображение (URL)</label>
              <input
                type="url"
                value={formData.image_url}
                onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                placeholder="https://example.com/image.jpg"
                disabled={saving}
              />
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  disabled={saving}
                />
                Товар активен
              </label>
            </div>

            {/* Улучшенная секция размеров */}
            <SizesSection
              formData={formData}
              handleSizeChange={handleSizeChange}
              addSize={addSize}
              removeSize={removeSize}
              saving={saving}
            />

            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={onCancel}
                disabled={saving}
              >
                Отмена
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={saving}
              >
                {saving ? (
                  <>
                    <div className="btn-spinner"></div>
                    Сохранение...
                  </>
                ) : (
                  product ? 'Сохранить' : 'Создать'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
      
      {/* Уведомления */}
      {notification && (
        <div className={`notification ${notification.type}`}>
          <div className="notification-content">
            <div className="notification-title">{notification.title}</div>
            <div className="notification-message">{notification.message}</div>
          </div>
          <button className="notification-close" onClick={() => setNotification(null)}>
            <FiX />
          </button>
        </div>
      )}
    </>
  );
};

export default ProductFormEnhanced;