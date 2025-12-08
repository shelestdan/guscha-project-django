import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import './ProductHeroBlock.css';

/**
 * Форматирует цену в формат "XXXX.XX ₽"
 */
export const formatPrice = (price) => {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price;
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

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.2, delayChildren: 0.05 }
    }
  };

  const textVariants = {
    hidden: { opacity: 0, x: -26 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.6, ease: 'easeOut' } }
  };

  const imageVariants = {
    hidden: { opacity: 0, scale: 0.96, x: 26 },
    visible: { opacity: 1, scale: 1, x: 0, transition: { duration: 0.7, ease: 'easeOut' } }
  };

  const collageVariants = {
    hidden: { opacity: 0, rotate: -4, x: 38 },
    visible: { opacity: 1, rotate: 2, x: 0, transition: { duration: 0.55, ease: 'easeOut', delay: 0.15 } }
  };

  return (
    <motion.section
      className="product-hero-block"
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.35 }}
      variants={containerVariants}
    >
      <div className="hero-grain-layer" aria-hidden="true" />
      <div className="hero-fiber-layer" aria-hidden="true" />

      <div className="hero-inner">
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

        <div className="hero-visual-wrap">
          <motion.div className="hero-photo-frame" variants={imageVariants}>
            <div className="hero-photo-clip">
              {!modelImageLoaded && !modelImageError && <div className="hero-skeleton" />}
              {modelImage && !modelImageError ? (
                <img
                  src={modelImage}
                  alt={`Модель в ${title}`}
                  className={`hero-photo-img ${modelImageLoaded ? 'loaded' : ''}`}
                  onError={() => setModelImageError(true)}
                  onLoad={() => setModelImageLoaded(true)}
                  loading="lazy"
                />
              ) : (
                <div className="hero-model-placeholder">
                  <span>Фото модели</span>
                </div>
              )}
            </div>
          </motion.div>

          <motion.div className="hero-sticker" variants={collageVariants}>
            <div className="hero-sticker-paper">
              {!productImageLoaded && !productImageError && (
                <div className="hero-skeleton hero-skeleton--sticker" />
              )}
              {productImage && !productImageError ? (
                <img
                  src={productImage}
                  alt={title}
                  className={`hero-sticker-img ${productImageLoaded ? 'loaded' : ''}`}
                  onError={() => setProductImageError(true)}
                  onLoad={() => setProductImageLoaded(true)}
                  loading="lazy"
                />
              ) : (
                <div className="hero-product-placeholder">
                  <span>Товар</span>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </motion.section>
  );
};

export default ProductHeroBlock;
