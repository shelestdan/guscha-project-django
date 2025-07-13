import React, { useEffect, Suspense, lazy, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import './styles/App.css';
import { Header, Footer } from './components/layout';
import { HomePage } from './pages';
import { CartSidebar } from './components/features/cart';
import { useCartStore } from './store/cartStore';
import ToastContainer from './components/ui/ToastContainer';

// Импортируем крупные страницы лениво
const Account = lazy(() => import('./components/Account'));
const ProductDetailPage = lazy(() => import('./pages/ProductDetailPage'));
const PreorderDetailPage = lazy(() => import('./pages/PreorderDetailPage'));
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'));
const OrderConfirmationPage = lazy(() => import('./pages/OrderConfirmationPage'));

function AppContent() {
  const location = useLocation();
  const isHome = location.pathname === '/';
  const fetchCart = useCartStore((state) => state.fetchCart);
  const mainRef = useRef(null);

  // Загружаем корзину при инициализации приложения
  useEffect(() => {
    console.log('🛒 Initializing cart on app start');
    fetchCart();
  }, [fetchCart]);

  return (
    <div className="App">
      <Header isHome={isHome} scrollContainerRef={mainRef} />
      <main ref={mainRef} style={{
        background: isHome ? 'transparent' : '#f1f1f1',
        minHeight: '100vh',
        paddingTop: 96,
        position: 'relative',
        zIndex: 1
      }}>
        <Suspense fallback={<div>Загрузка...</div>}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/products/:slug" element={<ProductDetailPage />} />
            <Route path="/preorders/:id" element={<PreorderDetailPage />} />
            <Route path="/account" element={<Account />} />
            <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="/order-confirmation/:orderId" element={<OrderConfirmationPage />} />
          </Routes>
        </Suspense>
        {isHome && <Footer />}
      </main>
      <CartSidebar />
      <ToastContainer position="top-right" />
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}