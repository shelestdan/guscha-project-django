import { useRef, useMemo } from 'react';
import { gsap } from 'gsap';
import './FlowingMenu.css';

/**
 * FlowingMenu Component
 * @param {Object[]} items - Array of menu items with link, text, image
 * @param {Function} onItemClick - Callback when item is clicked
 * @param {string|number} activeId - Currently active item id
 */
const FlowingMenu = ({ items = [], onItemClick, activeId }) => {
  return (
    <div className="flowing-menu-wrapper">
      <nav className="flowing-menu-nav">
        {items.map((item, idx) => (
          <MenuItem 
            key={item.id || idx} 
            {...item} 
            onItemClick={onItemClick}
            isActive={activeId === item.id}
          />
        ))}
      </nav>
    </div>
  );
};

const MenuItem = ({ id, text, image, onItemClick, isActive }) => {
  const itemRef = useRef(null);
  const marqueeRef = useRef(null);
  const marqueeInnerRef = useRef(null);

  const animationDefaults = { duration: 0.6, ease: 'expo' };

  const findClosestEdge = (mouseX, mouseY, width, height) => {
    const topEdgeDist = Math.pow(mouseX - width / 2, 2) + Math.pow(mouseY, 2);
    const bottomEdgeDist = Math.pow(mouseX - width / 2, 2) + Math.pow(mouseY - height, 2);
    return topEdgeDist < bottomEdgeDist ? 'top' : 'bottom';
  };

  const handleMouseEnter = (ev) => {
    if (!itemRef.current || !marqueeRef.current || !marqueeInnerRef.current) return;
    const rect = itemRef.current.getBoundingClientRect();
    const edge = findClosestEdge(ev.clientX - rect.left, ev.clientY - rect.top, rect.width, rect.height);
    
    const tl = gsap.timeline({ defaults: animationDefaults });
    tl.set(marqueeRef.current, { y: edge === 'top' ? '-101%' : '101%' })
      .set(marqueeInnerRef.current, { y: edge === 'top' ? '101%' : '-101%' })
      .to([marqueeRef.current, marqueeInnerRef.current], { y: '0%' });
  };

  const handleMouseLeave = (ev) => {
    if (!itemRef.current || !marqueeRef.current || !marqueeInnerRef.current) return;
    const rect = itemRef.current.getBoundingClientRect();
    const edge = findClosestEdge(ev.clientX - rect.left, ev.clientY - rect.top, rect.width, rect.height);
    
    const tl = gsap.timeline({ defaults: animationDefaults });
    tl.to(marqueeRef.current, { y: edge === 'top' ? '-101%' : '101%' })
      .to(marqueeInnerRef.current, { y: edge === 'top' ? '101%' : '-101%' }, '<');
  };

  const handleClick = (e) => {
    e.preventDefault();
    if (onItemClick) {
      onItemClick(id);
    }
  };

  // Создаём два идентичных набора для бесшовного цикла
  const repeatedMarqueeContent = useMemo(() => {
    const items = Array.from({ length: 6 }).map((_, idx) => (
      <span key={idx} className="flowing-menu-marquee-item">
        <span className="flowing-menu-marquee-text">{text}</span>
        {image && (
          <div 
            className="flowing-menu-marquee-image"
            style={{ backgroundImage: `url(${image})` }}
          />
        )}
      </span>
    ));
    return items;
  }, [text, image]);

  return (
    <div 
      className={`flowing-menu-item ${isActive ? 'active' : ''}`} 
      ref={itemRef}
    >
      <button
        className="flowing-menu-link"
        onClick={handleClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {text}
      </button>
      <div className="flowing-menu-marquee" ref={marqueeRef}>
        <div className="flowing-menu-marquee-inner" ref={marqueeInnerRef}>
          <div className="flowing-menu-marquee-content">
            {repeatedMarqueeContent}
            {repeatedMarqueeContent}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowingMenu;
