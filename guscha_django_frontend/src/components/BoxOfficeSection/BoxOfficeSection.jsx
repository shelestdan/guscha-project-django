import { useRef } from 'react';
import VariableProximity from '../VariableProximity';
import './BoxOfficeSection.css';

const BoxOfficeSection = () => {
  const containerRef = useRef(null);

  return (
    <section id="box-office" className="box-office-section">
      <div className="box-office-container" ref={containerRef}>
        <div className="box-office-content">
          <VariableProximity
            label="BOX OFFICE"
            className="box-office-text"
            fromFontVariationSettings="'wght' 400, 'opsz' 9"
            toFontVariationSettings="'wght' 800, 'opsz' 40"
            containerRef={containerRef}
            radius={250}
            falloff="linear"
          />
          <div className="box-office-number-container">
            <VariableProximity
              label="10 000 000"
              className="box-office-number"
              fromFontVariationSettings="'wght' 400, 'opsz' 9"
              toFontVariationSettings="'wght' 800, 'opsz' 40"
              containerRef={containerRef}
              radius={250}
              falloff="linear"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default BoxOfficeSection; 