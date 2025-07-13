import React from 'react';
import HeroSection from '../HeroSection';
import { ProductShowcase, ProductGrid } from '../components/features/products';
import BoxOfficeSection from '../components/BoxOfficeSection';

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <ProductShowcase />
      <div className="homepage-divider" />
      <div id="products">
        <ProductGrid />
      </div>
      <BoxOfficeSection />
    </>
  );
} 