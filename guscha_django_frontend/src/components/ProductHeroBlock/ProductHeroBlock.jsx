import { useState, useRef, useCallback, useMemo, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import GridDistortion from '../GridDistortion/GridDistortion';
import './ProductHeroBlock.css';

const ProductHeroBlock = memo(({
  title = 'КОЛЛЕКЦИЯ',
  subtitle = 'КАПСЕЛЬНАЯ КОЛЛЕКЦИЯ',
  description = '',
  modelImage = '',
  productImages = [],
  onPreorder,
  productId = null
}) => {
  const navigate = useNavigate();
  const sectionRef = useRef(null);
  const [modelImageLoaded, setModelImageLoaded] = useState(false);
  const [modelImageError, setModelImageError] = useState(false);
  const [loadedProducts, setLoadedProducts] = useState({});

  const handlePreorderClick = useCallback(() => {
    if (onPreorder) {
      onPreorder();
    } else if (productId) {
      navigate(`/preorders/${productId}`);
    }
  }, [onPreorder, productId, navigate]);

  const handleProductLoad = useCallback((index) => {
    setLoadedProducts(prev => ({ ...prev, [index]: true }));
  }, []);

  const handleModelLoad = useCallback(() => setModelImageLoaded(true), []);
  const handleModelError = useCallback(() => setModelImageError(true), []);

  // Мемоизируем варианты анимации - они статичны
  const containerVariants = useMemo(() => ({
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.1 }
    }
  }), []);

  const modelVariants = useMemo(() => ({
    hidden: { opacity: 0, x: -30 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.7, ease: 'easeOut' } }
  }), []);

  const imgVariants = useMemo(() => ({
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
  }), []);

  const textVariants = useMemo(() => ({
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, delay: 0.3 } }
  }), []);

  return (
    <motion.section
      className="category-diptych"
      ref={sectionRef}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      variants={containerVariants}
    >
      <div className="category-diptych__container">
        {/* Колонка 1 - большое фото модели с эффектом GridDistortion */}
        <motion.div className="category-diptych__col category-diptych__col--1" variants={modelVariants}>
          <div className="category-diptych__link">
            {modelImage && !modelImageError ? (
              <div className="category-diptych__image category-diptych__image--main category-diptych__image--distortion">
                <GridDistortion
                  imageSrc={modelImage}
                  grid={10}
                  mouse={0.1}
                  strength={0.15}
                  relaxation={0.9}
                  className="category-diptych__grid-distortion"
                />
              </div>
            ) : (
              <div className="category-diptych__placeholder">Фото</div>
            )}
          </div>
        </motion.div>

        {/* Колонка 2 - фото товаров + текст */}
        <div className="category-diptych__col category-diptych__col--2">
          {/* Контейнер с 2 фото, накладывающимися друг на друга */}
          <motion.div className="category-diptych__col--2-images" variants={imgVariants}>
            {productImages[0] && (
              <div className="category-diptych__image category-diptych__image--1">
                {!loadedProducts[0] && <div className="category-diptych__img-skeleton" />}
                <img
                  src={productImages[0]}
                  alt={`${title} 1`}
                  className={loadedProducts[0] ? 'loaded' : ''}
                  onLoad={() => handleProductLoad(0)}
                  width="279"
                  height="354"
                />
              </div>
            )}
            {productImages[1] && (
              <div className="category-diptych__image category-diptych__image--2">
                {!loadedProducts[1] && <div className="category-diptych__img-skeleton" />}
                <img
                  src={productImages[1]}
                  alt={`${title} 2`}
                  className={loadedProducts[1] ? 'loaded' : ''}
                  onLoad={() => handleProductLoad(1)}
                  width="279"
                  height="354"
                />
              </div>
            )}
          </motion.div>

          {/* Текстовый контент */}
          <motion.div className="category-diptych__col--2-content" variants={textVariants}>
            <h2 className="category-diptych__title">{title}</h2>
            <h3 className="category-diptych__subtitle">{subtitle}</h3>
            {description && (
              <div className="category-diptych__description">
                <p>{description}</p>
              </div>
            )}
            <button
              className="category-diptych__btn"
              onClick={handlePreorderClick}
              type="button"
            >
              ПРЕДЗАКАЗ
            </button>
          </motion.div>
        </div>
      </div>
    </motion.section>
  );
});

ProductHeroBlock.displayName = 'ProductHeroBlock';

export default ProductHeroBlock;
