import BackgroundContent from './components/BackgroundContent/BackgroundContent';
import './styles/App.css';

const HeroSection = () => {
  return (
    <section 
      className="hero-section hero-section-main" 
      style={{
        marginTop: -96,
        position: 'relative'
      }}
    >
      <BackgroundContent />
    </section>
  );
};

export default HeroSection;
