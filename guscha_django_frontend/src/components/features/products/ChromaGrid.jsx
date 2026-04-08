import { useRef, useEffect } from 'react';
import { gsap } from 'gsap';
import { Link } from 'react-router-dom';

/**
 * ChromaGrid Component
 * @param {Object[]} items - Array of product items
 * @param {string} className - Additional CSS class
 * @param {number} radius - Spotlight radius
 * @param {number} damping - Animation damping
 * @param {number} fadeOut - Fade out duration
 * @param {string} ease - GSAP easing function
 */
const ChromaGrid = ({
  items = [],
  className = '',
  radius = 300,
  damping = 0.45,
  fadeOut = 0.6,
  ease = 'power3.out'
}) => {
  const rootRef = useRef(null);
  const fadeRef = useRef(null);
  const setX = useRef(null);
  const setY = useRef(null);
  const pos = useRef({ x: 0, y: 0 });

  // Цвета для градиентов карточек (заканчиваются на #111111 для бесшовного перехода)
  const colors = [
    { border: '#4F46E5', gradient: 'linear-gradient(145deg,#4F46E5,#111111)' },
    { border: '#10B981', gradient: 'linear-gradient(210deg,#10B981,#111111)' },
    { border: '#F59E0B', gradient: 'linear-gradient(165deg,#F59E0B,#111111)' },
    { border: '#EF4444', gradient: 'linear-gradient(195deg,#EF4444,#111111)' },
    { border: '#8B5CF6', gradient: 'linear-gradient(225deg,#8B5CF6,#111111)' },
    { border: '#06B6D4', gradient: 'linear-gradient(135deg,#06B6D4,#111111)' },
  ];

  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;

    setX.current = gsap.quickSetter(el, '--x', 'px');
    setY.current = gsap.quickSetter(el, '--y', 'px');

    const { width, height } = el.getBoundingClientRect();
    pos.current = { x: width / 2, y: height / 2 };
    setX.current(pos.current.x);
    setY.current(pos.current.y);
  }, []);

  const moveTo = (x, y) => {
    gsap.to(pos.current, {
      x,
      y,
      duration: damping,
      ease,
      onUpdate: () => {
        setX.current?.(pos.current.x);
        setY.current?.(pos.current.y);
      },
      overwrite: true
    });
  };

  const handleMove = (e) => {
    const r = rootRef.current.getBoundingClientRect();
    moveTo(e.clientX - r.left, e.clientY - r.top);
    gsap.to(fadeRef.current, { opacity: 0, duration: 0.25, overwrite: true });
  };

  const handleLeave = () => {
    gsap.to(fadeRef.current, {
      opacity: 1,
      duration: fadeOut,
      overwrite: true
    });
  };

  const handleCardMove = (e) => {
    const c = e.currentTarget;
    const rect = c.getBoundingClientRect();
    c.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
    c.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
  };

  return (
    <div
      ref={rootRef}
      onPointerMove={handleMove}
      onPointerLeave={handleLeave}
      className={`chroma-grid-root ${className}`}
      style={{
        '--r': `${radius}px`,
        '--x': '50%',
        '--y': '50%'
      }}
    >
      {items.map((item, i) => {
        const colorSet = colors[i % colors.length];
        const borderColor = item.borderColor || colorSet.border;
        const gradient = item.gradient || colorSet.gradient;
        
        return (
          <Link
            key={item.id || i}
            to={`/products/${item.slug || item.id}`}
            className="chroma-card"
            onMouseMove={handleCardMove}
            style={{
              '--card-border': borderColor,
              background: gradient,
              '--spotlight-color': 'rgba(255,255,255,0.3)'
            }}
          >
            <div className="chroma-card-spotlight" />
            <div className="chroma-card-image-wrapper">
              <img 
                src={item.image} 
                alt={item.title} 
                loading="lazy" 
                className="chroma-card-image"
                onContextMenu={(e) => e.preventDefault()}
                onDragStart={(e) => e.preventDefault()}
                draggable="false"
              />
            </div>
            <footer className="chroma-card-footer">
              <div className="chroma-card-info">
                <h3 className="chroma-card-title">{item.title}</h3>
                <span className="chroma-card-price">{item.price} ₽</span>
              </div>
              {item.sizes && item.sizes.length > 0 && (
                <div className="chroma-card-sizes">
                  {item.sizes.map((size) => (
                    <span 
                      key={size.id || size.size_name}
                      className={`chroma-size-badge ${size.is_available ? 'in-stock' : 'out-of-stock'}`}
                      title={size.is_available ? 'В наличии' : 'Нет в наличии'}
                    >
                      {size.size_name}
                    </span>
                  ))}
                </div>
              )}
            </footer>
          </Link>
        );
      })}

      {/* Grayscale overlay */}
      <div
        className="chroma-overlay"
        style={{
          backdropFilter: 'grayscale(1)',
          WebkitBackdropFilter: 'grayscale(1)',
          background: 'transparent',
          maskImage:
            'radial-gradient(circle var(--r) at var(--x) var(--y),transparent 0%,transparent 15%,rgba(0,0,0,0.10) 30%,rgba(0,0,0,0.22)45%,rgba(0,0,0,0.35)60%,rgba(0,0,0,0.50)75%,rgba(0,0,0,0.68)88%,white 100%)',
          WebkitMaskImage:
            'radial-gradient(circle var(--r) at var(--x) var(--y),transparent 0%,transparent 15%,rgba(0,0,0,0.10) 30%,rgba(0,0,0,0.22)45%,rgba(0,0,0,0.35)60%,rgba(0,0,0,0.50)75%,rgba(0,0,0,0.68)88%,white 100%)'
        }}
      />

      {/* Fade overlay */}
      <div
        ref={fadeRef}
        className="chroma-fade-overlay"
        style={{
          backdropFilter: 'grayscale(1)',
          WebkitBackdropFilter: 'grayscale(1)',
          background: 'transparent',
          maskImage:
            'radial-gradient(circle var(--r) at var(--x) var(--y),white 0%,white 15%,rgba(255,255,255,0.90)30%,rgba(255,255,255,0.78)45%,rgba(255,255,255,0.65)60%,rgba(255,255,255,0.50)75%,rgba(255,255,255,0.32)88%,transparent 100%)',
          WebkitMaskImage:
            'radial-gradient(circle var(--r) at var(--x) var(--y),white 0%,white 15%,rgba(255,255,255,0.90)30%,rgba(255,255,255,0.78)45%,rgba(255,255,255,0.65)60%,rgba(255,255,255,0.50)75%,rgba(255,255,255,0.32)88%,transparent 100%)',
          opacity: 1
        }}
      />
    </div>
  );
};

export default ChromaGrid;
