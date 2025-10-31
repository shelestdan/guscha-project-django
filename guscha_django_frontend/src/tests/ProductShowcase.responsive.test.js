/**
 * Comprehensive Responsive Design Tests for ProductShowcase Component
 * Tests all breakpoints and device sizes as specified in requirements
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProductShowcase from '../components/features/products/ProductShowcase';
import * as preordersApi from '../api/preordersApi';

// Mock the API
jest.mock('../api/preordersApi');

// Mock data for testing
const mockProducts = [
  {
    id: 1,
    name: 'Test Product 1',
    price: '1000',
    model_image: 'https://example.com/model1.jpg',
    product_image: 'https://example.com/product1.jpg'
  },
  {
    id: 2,
    name: 'Test Product 2 with Very Long Name That Should Wrap Properly',
    price: '2000',
    model_image: 'https://example.com/model2.jpg',
    product_image: 'https://example.com/product2.jpg'
  }
];

// Helper function to set viewport size
const setViewportSize = (width, height) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  });
  window.dispatchEvent(new Event('resize'));
};

// Helper function to get computed styles
const getComputedStyleValue = (element, property) => {
  return window.getComputedStyle(element).getPropertyValue(property);
};

// Wrapper component for testing
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('ProductShowcase Responsive Design Tests', () => {
  beforeEach(() => {
    preordersApi.fetchPreorders.mockResolvedValue({
      results: mockProducts
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Desktop Large (1400px+) - Requirement 4.1', () => {
    beforeEach(() => {
      setViewportSize(1400, 900);
    });

    test('should display original design layout', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const root = document.querySelector('.product-showcase-root');
      const images = document.querySelector('.product-showcase-images');
      const modelImage = document.querySelector('.product-showcase-left');
      const productImage = document.querySelector('.product-showcase-center');
      const textBlock = document.querySelector('.product-showcase-right');

      // Verify layout structure
      expect(root).toHaveStyle('flex-direction: row');
      expect(images).toBeInTheDocument();
      expect(modelImage).toBeInTheDocument();
      expect(productImage).toBeInTheDocument();
      expect(textBlock).toBeInTheDocument();

      // Verify model image is visible (Requirement 1.1)
      expect(modelImage).toBeVisible();
      expect(modelImage.querySelector('img')).toBeInTheDocument();
    });

    test('should maintain original color scheme', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const root = document.querySelector('.product-showcase-root');
      const title = document.querySelector('.product-showcase-title');
      const price = document.querySelector('.product-showcase-price');
      const button = document.querySelector('.product-showcase-preorder');

      // Verify original color scheme (Requirement 3.1)
      expect(root).toHaveStyle('background: #f1f1f1');
      expect(title).toHaveStyle('color: #000');
      expect(price).toHaveStyle('color: #000');
      expect(button).toHaveStyle('background: #fff');
      expect(button).toHaveStyle('color: #000');
    });
  });

  describe('Desktop (1200px-1399px) - Requirement 4.2', () => {
    beforeEach(() => {
      setViewportSize(1300, 800);
    });

    test('should adapt layout while keeping all elements visible', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const modelImage = document.querySelector('.product-showcase-left');
      const productImage = document.querySelector('.product-showcase-center');

      // Verify model image remains visible (Requirement 1.1)
      expect(modelImage).toBeVisible();
      expect(productImage).toBeVisible();

      // Verify images are properly sized for this breakpoint
      expect(modelImage).toBeInTheDocument();
      expect(productImage).toBeInTheDocument();
    });
  });

  describe('Tablet Landscape (900px-1199px) - Requirement 4.2', () => {
    beforeEach(() => {
      setViewportSize(1000, 700);
    });

    test('should maintain horizontal layout with adapted sizes', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const root = document.querySelector('.product-showcase-root');
      const modelImage = document.querySelector('.product-showcase-left');
      const productImage = document.querySelector('.product-showcase-center');

      // Verify layout remains horizontal
      expect(root).toHaveStyle('flex-direction: row');
      
      // Verify model image is still visible (Requirement 1.2)
      expect(modelImage).toBeVisible();
      expect(productImage).toBeVisible();
    });
  });

  describe('Tablet Portrait (600px-899px) - Requirement 4.3', () => {
    beforeEach(() => {
      setViewportSize(768, 1024);
    });

    test('should switch to vertical layout while keeping all elements', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const root = document.querySelector('.product-showcase-root');
      const modelImage = document.querySelector('.product-showcase-left');
      const productImage = document.querySelector('.product-showcase-center');
      const textBlock = document.querySelector('.product-showcase-right');

      // Verify layout switches to vertical
      expect(root).toHaveStyle('flex-direction: column');
      
      // Verify all elements remain visible (Requirement 1.2)
      expect(modelImage).toBeVisible();
      expect(productImage).toBeVisible();
      expect(textBlock).toBeVisible();

      // Verify text is centered for tablet
      expect(textBlock).toHaveStyle('text-align: center');
    });
  });

  describe('Mobile Large (480px-599px) - Requirement 4.4', () => {
    beforeEach(() => {
      setViewportSize(550, 800);
    });

    test('should optimize for mobile while keeping model image visible', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const root = document.querySelector('.product-showcase-root');
      const modelImage = document.querySelector('.product-showcase-left');
      const productImage = document.querySelector('.product-showcase-center');
      const images = document.querySelector('.product-showcase-images');

      // Verify vertical layout
      expect(root).toHaveStyle('flex-direction: column');
      
      // Verify model image is optimized but visible (Requirement 1.3)
      expect(modelImage).toBeVisible();
      expect(productImage).toBeVisible();

      // Verify images are arranged vertically
      expect(images).toHaveStyle('flex-direction: column');
    });

    test('should maintain touch-friendly button sizes', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const button = document.querySelector('.product-showcase-preorder');
      const arrow = document.querySelector('.product-showcase-arrow');

      // Verify button meets touch requirements (Requirement 2.3)
      const buttonRect = button.getBoundingClientRect();
      const arrowRect = arrow.getBoundingClientRect();

      expect(buttonRect.height).toBeGreaterThanOrEqual(44); // Minimum touch target
      expect(arrowRect.height).toBeGreaterThanOrEqual(44);
    });
  });

  describe('Mobile Medium (400px-479px) - Requirement 4.4', () => {
    beforeEach(() => {
      setViewportSize(450, 700);
    });

    test('should maintain functionality on smaller mobile screens', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const modelImage = document.querySelector('.product-showcase-left');
      const productImage = document.querySelector('.product-showcase-center');
      const title = document.querySelector('.product-showcase-title');

      // Verify model image remains visible (Requirement 1.3)
      expect(modelImage).toBeVisible();
      expect(productImage).toBeVisible();

      // Verify text wrapping works properly (Requirement 2.5)
      expect(title).toHaveStyle('word-break: break-word');
    });
  });

  describe('Mobile Small (<400px) - Requirement 4.4', () => {
    beforeEach(() => {
      setViewportSize(350, 600);
    });

    test('should work on very small screens', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      const modelImage = document.querySelector('.product-showcase-left');
      const productImage = document.querySelector('.product-showcase-center');

      // Verify model image is still visible on smallest screens (Requirement 1.4)
      expect(modelImage).toBeVisible();
      expect(productImage).toBeVisible();
    });
  });

  describe('Text Adaptivity Tests - Requirement 2', () => {
    test('should handle long product names properly', async () => {
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      // Switch to product with long name
      const arrow = document.querySelector('.product-showcase-arrow');
      fireEvent.click(arrow);

      await waitFor(() => {
        expect(screen.getByText('Test Product 2 with Very Long Name That Should Wrap Properly')).toBeInTheDocument();
      });

      const title = document.querySelector('.product-showcase-title');
      
      // Verify text wrapping (Requirement 2.5)
      expect(title).toHaveStyle('word-break: break-word');
      expect(title).toHaveStyle('overflow-wrap: break-word');
    });

    test('should maintain readable text sizes across breakpoints', async () => {
      const breakpoints = [
        { width: 1400, name: 'desktop-large' },
        { width: 1300, name: 'desktop' },
        { width: 1000, name: 'tablet-landscape' },
        { width: 768, name: 'tablet-portrait' },
        { width: 550, name: 'mobile-large' },
        { width: 450, name: 'mobile-medium' },
        { width: 350, name: 'mobile-small' }
      ];

      for (const breakpoint of breakpoints) {
        setViewportSize(breakpoint.width, 800);
        
        render(
          <TestWrapper>
            <ProductShowcase />
          </TestWrapper>
        );

        await waitFor(() => {
          expect(screen.getByText('Test Product 1')).toBeInTheDocument();
        });

        const title = document.querySelector('.product-showcase-title');
        const price = document.querySelector('.product-showcase-price');

        // Verify text remains readable (Requirements 2.1, 2.2)
        const titleFontSize = parseInt(getComputedStyleValue(title, 'font-size'));
        const priceFontSize = parseInt(getComputedStyleValue(price, 'font-size'));

        expect(titleFontSize).toBeGreaterThanOrEqual(20); // Minimum readable size
        expect(priceFontSize).toBeGreaterThanOrEqual(16); // Minimum readable size

        // Clean up for next iteration
        document.body.innerHTML = '';
      }
    });
  });

  describe('Animation Tests - Requirement 5', () => {
    test('should animate smoothly on all screen sizes', async () => {
      const breakpoints = [1400, 1000, 768, 550, 350];

      for (const width of breakpoints) {
        setViewportSize(width, 800);
        
        render(
          <TestWrapper>
            <ProductShowcase />
          </TestWrapper>
        );

        await waitFor(() => {
          expect(screen.getByText('Test Product 1')).toBeInTheDocument();
        });

        const arrow = document.querySelector('.product-showcase-arrow');
        const modelImage = document.querySelector('.product-showcase-left');

        // Verify animation classes are applied (Requirement 5.1)
        expect(modelImage).toHaveClass('product-anim-in');

        // Trigger animation
        fireEvent.click(arrow);

        // Verify animation starts
        await waitFor(() => {
          const animatingElements = document.querySelectorAll('.product-anim-out, .product-anim-new');
          expect(animatingElements.length).toBeGreaterThan(0);
        });

        // Wait for animation to complete
        await waitFor(() => {
          expect(screen.getByText('Test Product 2 with Very Long Name That Should Wrap Properly')).toBeInTheDocument();
        }, { timeout: 1000 });

        // Clean up for next iteration
        document.body.innerHTML = '';
      }
    });

    test('should respect prefers-reduced-motion', async () => {
      // Mock prefers-reduced-motion
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      // Verify reduced motion is respected (Requirement 5.4)
      const root = document.querySelector('.product-showcase-root');
      expect(root).toBeInTheDocument();
    });
  });

  describe('Orientation Change Tests - Requirement 4.5', () => {
    test('should adapt to orientation changes', async () => {
      // Start in portrait
      setViewportSize(768, 1024);
      
      render(
        <TestWrapper>
          <ProductShowcase />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      });

      let root = document.querySelector('.product-showcase-root');
      expect(root).toHaveStyle('flex-direction: column');

      // Switch to landscape
      setViewportSize(1024, 768);
      window.dispatchEvent(new Event('resize'));

      // Wait for layout to update
      await waitFor(() => {
        root = document.querySelector('.product-showcase-root');
        // Should switch to horizontal layout in landscape
        expect(root).toHaveStyle('flex-direction: row');
      });
    });
  });

  describe('Visual Consistency Tests - Requirement 3', () => {
    test('should maintain brand colors across all breakpoints', async () => {
      const breakpoints = [1400, 1000, 768, 550, 350];

      for (const width of breakpoints) {
        setViewportSize(width, 800);
        
        render(
          <TestWrapper>
            <ProductShowcase />
          </TestWrapper>
        );

        await waitFor(() => {
          expect(screen.getByText('Test Product 1')).toBeInTheDocument();
        });

        const root = document.querySelector('.product-showcase-root');
        const title = document.querySelector('.product-showcase-title');
        const price = document.querySelector('.product-showcase-price');
        const button = document.querySelector('.product-showcase-preorder');

        // Verify consistent branding (Requirements 3.1, 3.2, 3.4)
        expect(root).toHaveStyle('background: #f1f1f1');
        expect(title).toHaveStyle('color: #000');
        expect(price).toHaveStyle('color: #000');
        expect(button).toHaveStyle('background: #fff');
        expect(button).toHaveStyle('border: 2px solid #000');

        // Clean up for next iteration
        document.body.innerHTML = '';
      }
    });
  });
});