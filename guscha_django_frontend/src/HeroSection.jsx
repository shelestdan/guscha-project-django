import { useRef, useEffect } from 'react';
import { motion, useScroll, useTransform, useSpring, useMotionValue } from 'framer-motion';
import BackgroundContent from './components/BackgroundContent/BackgroundContent';
import './styles/App.css';
import './styles/HeroParallax.css';

const HeroSection = () => {
  const containerRef = useRef(null);
  
  // Mouse parallax
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Smooth spring physics
  const springConfig = { damping: 25, stiffness: 120 };
  const mouseXSpring = useSpring(mouseX, springConfig);
  const mouseYSpring = useSpring(mouseY, springConfig);

  // Scroll-based parallax
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  // Parallax transforms
  const bgY = useTransform(scrollYProgress, [0, 1], ['0%', '40%']);
  const bgScale = useTransform(scrollYProgress, [0, 1], [1, 1.15]);
  const overlayOpacity = useTransform(scrollYProgress, [0, 0.5], [0, 0.3]);
  const contentY = useTransform(scrollYProgress, [0, 1], ['0%', '25%']);
  
  // Floating elements parallax
  const float1Y = useTransform(scrollYProgress, [0, 1], ['0%', '-30%']);
  const float2Y = useTransform(scrollYProgress, [0, 1], ['0%', '-50%']);
  const float3Y = useTransform(scrollYProgress, [0, 1], ['0%', '-20%']);

  // Mouse-based transforms
  const bgXMouse = useTransform(mouseXSpring, v => v * 0.5);
  const bgYMouse = useTransform(mouseYSpring, v => v * 0.3);
  const float1XMouse = useTransform(mouseXSpring, v => v * 1.2);
  const float1YMouse = useTransform(mouseYSpring, v => v * 1.2);
  const float2XMouse = useTransform(mouseXSpring, v => v * -0.8);
  const float2YMouse = useTransform(mouseYSpring, v => v * -0.8);
  const float3XMouse = useTransform(mouseXSpring, v => v * 0.6);

  // Mouse move handler
  useEffect(() => {
    const handleMouseMove = (e) => {
      const { clientX, clientY } = e;
      const { innerWidth, innerHeight } = window;
      
      const x = (clientX / innerWidth - 0.5) * 2;
      const y = (clientY / innerHeight - 0.5) * 2;
      
      mouseX.set(x * 15);
      mouseY.set(y * 15);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [mouseX, mouseY]);

  return (
    <section 
      ref={containerRef}
      className="hero-section hero-section-main hero-parallax" 
      style={{
        marginTop: -96,
        position: 'relative'
      }}
    >
      {/* Parallax Background Layer */}
      <motion.div 
        className="parallax-bg-wrapper"
        style={{ 
          y: bgY, 
          scale: bgScale,
          x: bgXMouse,
        }}
      >
        <BackgroundContent />
      </motion.div>

      {/* Gradient Overlay on scroll */}
      <motion.div 
        className="parallax-scroll-overlay"
        style={{ opacity: overlayOpacity }}
      />

      {/* Floating Decorative Elements */}
      <motion.div 
        className="parallax-float parallax-float-1"
        style={{ y: float1Y, x: float1XMouse }}
      />
      <motion.div 
        className="parallax-float parallax-float-2"
        style={{ y: float2Y, x: float2XMouse }}
      />
      <motion.div 
        className="parallax-float parallax-float-3"
        style={{ y: float3Y, x: float3XMouse }}
      />

      {/* Animated Lines */}
      <motion.div 
        className="parallax-line parallax-line-1"
        style={{ y: float1Y }}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1.2, delay: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      />
      <motion.div 
        className="parallax-line parallax-line-2"
        style={{ y: float2Y }}
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
        transition={{ duration: 1, delay: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
      />

      {/* Grain Texture Overlay */}
      <div className="parallax-grain" />

      {/* Scroll Indicator */}
      <motion.div 
        className="parallax-scroll-indicator"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5, duration: 0.6 }}
      >
        <motion.div 
          className="scroll-mouse"
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        >
          <div className="scroll-wheel" />
        </motion.div>
        <span className="scroll-text">Scroll</span>
      </motion.div>
    </section>
  );
};

export default HeroSection;
