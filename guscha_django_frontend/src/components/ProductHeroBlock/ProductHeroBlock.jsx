import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import './ProductHeroBlock.css';

/**
 * Форматирует цену в формат "XXXX.XX ₽"
 */
export const formatPrice = (price) => {
  let numPrice = typeof price === 'string' ? parseFloat(price) : price;
  if (isNaN(numPrice) || numPrice === null || numPrice === undefined) {
    return '0.00 ₽';
  }
  return `${numPrice.toFixed(2)} ₽`;
};

const ProductHeroBlock = ({
  title = 'ДЖИНСЫ',
  price = 7900,
  modelImage = '',
  productImage = '',
  description = '',
  composition = '',
  color = '',
  care = '',
  onPreorder,
  onNavigate,
  productId = null
}) => {
  const navigate = useNavigate();
  const [modelImageError, setModelImageError] = useState(false);
  const [productImageError, setProductImageError] = useState(false);
  const [modelImageLoaded, setModelImageLoaded] = useState(false);
  const [productImageLoaded, setProductImageLoaded] = useState(false);

  const handlePreorderClick = () => {
    if (onPreorder) {
      onPreorder();
    } else if (productId) {
      navigate(`/preorders/${productId}`);
    }
  };

  const handleNavigateClick = () => {
    if (onNavigate) {
      onNavigate();
    } else if (productId) {
      navigate(`/preorders/${productId}`);
    }
  };

  // Анимации
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15, delayChildren: 0.1 }
    }
  };

  const textVariants = {
    hidden: { opacity: 0, x: -30 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.6, ease: 'easeOut' } }
  };

  const imageVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.7, ease: 'easeOut' } }
  };

  const collageVariants = {
    hidden: { opacity: 0, rotate: -5, x: 30 },
    visible: { opacity: 1, rotate: 2, x: 0, transition: { duration: 0.6, ease: 'easeOut', delay: 0.3 } }
  };

  const descriptionVariants = {
    hidden: { opacity: 0, x: 20 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.5, ease: 'easeOut', delay: 0.4 } }
  };

  return (
    <motion.section 
      className="product-hero-block"
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      variants={containerVariants}
    >
      {/* Текстурный оверлей для бумажного эффекта */}
      <div className="hero-texture-overlay" />

      {/* Левая часть - текстовая информация */}
      <motion.div className="hero-text-section" variants={textVariants}>
        <h1 className="hero-title">{title}</h1>
        <p className="hero-price">{formatPrice(price)}</p>
        
        <motion.button 
          className="hero-preorder-btn"
          onClick={handlePreorderClick}
          type="button"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          ПРЕДЗАКАЗ
        </motion.button>
        
        <motion.button 
          className="hero-arrow-btn"
          onClick={handleNavigateClick}
          type="button"
          aria-label="Перейти к товару"
          whileHover={{ x: 5 }}
        >
          →
        </motion.button>
      </motion.div>

      {/* Правая часть - визуальный блок */}
      <div className="hero-visual-section">
        {/* Шестиугольный контейнер с фото модели */}
        <motion.div className="hero-hexagon-container" variants={imageVariants}>
          <div className="hero-hexagon-mask">
            {!modelImageLoaded && !modelImageError && (
              <div className="hero-skeleton" />
            )}
            {modelImage && !modelImageError ? (
              <img
                src={modelImage}
                alt={`Модель в ${title}`}
                className={`hero-model-img ${modelImageLoaded ? 'loaded' : ''}`}
                onError={() => setModelImageError(true)}
                onLoad={() => setModelImageLoaded(true)}
              />
            ) : (
              <div className="hero-model-placeholder">
                <span>Фото модели</span>
              </div>
            )}
          </div>
        </motion.div>

        {/* Коллаж-элемент: джинсы на рваной бумаге */}
        <motion.div className="hero-collage-element" variants={collageVariants}>
          <div className="hero-torn-paper">
            <svg className="hero-torn-edge" viewBox="0 0 100 200" preserveAspectRatio="none">
              <path d="M0,0 L100,0 L100,200 L0,200 Z" fill="#c9c4b8"/>
              <path d="M95,0 Q98,20 92,40 Q100,60 94,80 Q99,100 93,120 Q100,140 95,160 Q98,180 93,200 L100,200 L100,0 Z" fill="#b8b3a7"/>
            </svg>
            <div className="hero-collage-inner">
              {!productImageLoaded && !productImageError && (
                <div className="hero-skeleton hero-skeleton--dark" />
              )}
              {productImage && !productImageError ? (
                <img
                  src={productImage}
                  alt={title}
                  className={`hero-product-img ${productImageLoaded ? 'loaded' : ''}`}
                  onError={() => setProductImageError(true)}
                  onLoad={() => setProductImageLoaded(true)}
                />
              ) : (
                <div className="hero-product-placeholder">
                  <span>Товар</span>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Блок описания справа */}
      {description && (
        <motion.div className="hero-description-section" variants={descriptionVariants}>
          <h3 className="hero-description-title">ОПИСАНИЕ</h3>
          <p className="hero-description-text">{description}</p>
          
          {(composition || color || care) && (
            <div className="hero-description-specs">
              {composition && (
                <p className="hero-spec-item">
                  <span className="hero-spec-label">Состав:</span> {composition}
                </p>
              )}
              {color && (
                <p className="hero-spec-item">
                  <span className="hero-spec-label">Цвет:</span> {color}
                </p>
              )}
              {care && (
                <p className="hero-spec-item">
                  <span className="hero-spec-label">Уход:</span> {care}
                </p>
              )}
            </div>
          )}
        </motion.div>
      )}
    </motion.section>
  );
};

export default ProductHeroBlock;
