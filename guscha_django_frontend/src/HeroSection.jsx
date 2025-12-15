import { useEffect, useRef, useState, useCallback } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import heroImage from './assets/images/Guscha_back.png';
import backgroundApi from './api/backgroundApi';
import VideoPlayer from './components/VideoPlayer';
import './styles/App.css';
import './styles/HeroParallax.css';

// Регистрируем плагин один раз
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

const preloadImage = (url) =>
  new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(url);
    img.onerror = reject;
    img.src = url;
  });

const HeroSection = () => {
  const containerRef = useRef(null);
  const rightRef = useRef(null);
  const logoRef = useRef(null);
  const primaryCopyRef = useRef(null);
  const secondaryCopyRef = useRef(null);
  const [bgUrl, setBgUrl] = useState(null);
  const [videoData, setVideoData] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const loadBg = async () => {
      let candidateUrl = null;

      try {
        const res = await backgroundApi.getActiveBackground();
        const data = res?.data;

        if (data?.content_type === 'video') {
          // Для видео сохраняем данные для отображения в правой части
          const videoUrl = data.platform === 'file'
            ? data.embed_url
            : (data.video_url || data.embed_url);
          if (isMounted) {
            setVideoData({
              url: videoUrl,
              loop: data.loop !== false,
              platform: data.platform
            });
          }
          return;
        } else if (data?.content_type === 'image' && data.image_url) {
          candidateUrl = data.image_url;
        } else if (data?.content_type === 'slideshow' && data.images?.length) {
          const primary = data.images.find((i) => i.is_primary) || data.images[0];
          candidateUrl = primary?.image_url || null;
        }
      } catch (e) {
        // keep fallback logic below
      }

      // Иначе используем полученный URL
      const finalUrl = candidateUrl;

      if (!finalUrl) {
        if (isMounted) setBgUrl(null);
        return;
      }

      try {
        await preloadImage(finalUrl);
        if (isMounted) setBgUrl(finalUrl);
      } catch (e) {
        if (isMounted) setBgUrl(null);
      }
    };

    loadBg();

    return () => {
      isMounted = false;
    };
  }, []);

  // Объединённый useEffect для всех GSAP анимаций - избегаем множественных контекстов
  useEffect(() => {
    if (!containerRef.current) return undefined;

    const ctx = gsap.context(() => {
      // === INTRO ANIMATIONS ===
      const tl = gsap.timeline({ defaults: { ease: 'power2.out' }, delay: 0.2 });

      // Чёрная панель собирается
      tl.from('.hero-split-left', {
        clipPath: 'inset(0 100% 0 0)',
        duration: 0.6,
      });

      // Текст слева по очереди
      tl.from(
        '.hero-left-inner > *',
        {
          y: 24,
          opacity: 0,
          stagger: 0.12,
          duration: 0.5,
        },
        '-=0.2'
      );

      // Фото справа
      if (rightRef.current) {
        tl.from(
          rightRef.current,
          {
            opacity: 0,
            scale: 1.06,
            y: 20,
            duration: 0.6,
          },
          '-=0.25'
        );
      }

      // Надпись RAVIX (обёртка)
      if (logoRef.current) {
        tl.from(
          logoRef.current,
          {
            opacity: 0,
            y: -12,
            duration: 0.55,
          },
          '-=0.35'
        );
      }

      // === SCROLL PARALLAX ANIMATIONS ===
      const createConfig = (overrides = {}) => ({
        trigger: containerRef.current,
        start: 'top top',
        end: '+=160%',
        scrub: 1.2,
        ...overrides,
      });

      // Логотип — без параллакса (фиксированная позиция)
      if (logoRef.current) {
        gsap.set(logoRef.current, { yPercent: 0 });
      }

      // Основной текст - сильно отстаёт от скролла
      if (primaryCopyRef.current) {
        gsap.fromTo(
          primaryCopyRef.current,
          { yPercent: 0 },
          {
            yPercent: 140,
            ease: 'none',
            scrollTrigger: createConfig({ end: '+=140%' }),
          }
        );
      }

      // Вторичный текст - ещё больше отстаёт (каскадный эффект)
      if (secondaryCopyRef.current) {
        gsap.fromTo(
          secondaryCopyRef.current,
          { yPercent: 0 },
          {
            yPercent: 180,
            ease: 'none',
            scrollTrigger: createConfig({ start: 'top+=30 top', end: '+=130%' }),
          }
        );
      }

      // Фотография - быстрая реакция на скролл
      if (rightRef.current) {
        gsap.fromTo(
          rightRef.current,
          { yPercent: 0 },
          {
            yPercent: 35,
            ease: 'none',
            scrollTrigger: createConfig({
              end: '+=140%',
              scrub: 0.3,
            }),
          }
        );
      }
    }, containerRef);

    return () => {
      ctx.revert();
      // Дополнительная очистка ScrollTrigger instances
      ScrollTrigger.getAll().forEach(trigger => {
        if (trigger.vars.trigger === containerRef.current) {
          trigger.kill();
        }
      });
    };
  }, []);

  return (
    <section ref={containerRef} className="hero-section hero-split">
      <div className="hero-logo-overlay" ref={logoRef}>
        RAVIX
      </div>

      <div className="hero-split-left">
        <div className="hero-left-inner">
          <p className="hero-left-copy" ref={primaryCopyRef}>
            REWRITE THE RULES
            <br />
            UNAPOLOGETIC STYLE,
            <br />
            FEARLESS VIBE
          </p>
          <p className="hero-left-copy hero-left-copy--secondary" ref={secondaryCopyRef}>
            BEYOND LIMITS
            <br />
            PURE ADRENALINE
            <br />
            OWN THE MOMENT
          </p>
        </div>
      </div>

      <div
        className="hero-split-right"
        ref={rightRef}
        style={bgUrl ? { backgroundImage: `url(${bgUrl})` } : undefined}
      >
        {videoData && (
          <VideoPlayer
            url={videoData.url}
            autoplay={true}
            muted={true}
            loop={videoData.loop}
            className="hero-video-player"
          />
        )}
      </div>
    </section>
  );
};

export default HeroSection;
