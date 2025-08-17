import React, { useEffect, Suspense, lazy, useRef, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import './styles/App.css';
import { Header, Footer } from './components/layout';
import { HomePage } from './pages';
import { CartSidebar } from './components/features/cart';

import { useCartStore } from './store/cartStore';
import { useAuth } from './hooks/useAuth';
import ToastContainer from './components/ui/ToastContainer';
import scrollBackgroundToggle from './utils/scrollBackgroundToggle';

// Импортируем крупные страницы лениво
const Account = lazy(() => import('./components/Account'));
const ProductDetailPage = lazy(() => import('./pages/ProductDetailPage'));
const PreorderDetailPage = lazy(() => import('./pages/PreorderDetailPage'));
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'));
const OrderConfirmationPage = lazy(() => import('./pages/OrderConfirmationPage'));
const AddressesPage = lazy(() => import('./pages/AddressesPage'));
const CollectionsPage = lazy(() => import('./pages/CollectionsPage'));
const CollectionDetailPage = lazy(() => import('./pages/CollectionDetailPage'));
const PasswordResetConfirm = lazy(() => import('./components/PasswordResetConfirm'));
const GoogleOAuthCallback = lazy(() => import('./components/GoogleOAuthCallback'));

function AppContent() {
  console.log('🚀 APP CONTENT RENDERED!');
  const location = useLocation();
  const isHome = location.pathname === '/';
  console.log('🏠 isHome:', isHome, 'pathname:', location.pathname);
  const fetchCart = useCartStore((state) => state.fetchCart);
  const mainRef = useRef(null);
  const [isBurgerMenuOpen, setIsBurgerMenuOpen] = useState(false);
  
  // Инициализируем аутентификацию для проверки токена при загрузке
  const { loading } = useAuth();

  // Загружаем корзину при инициализации приложения
  useEffect(() => {
    console.log('🛒 Initializing cart on app start');
    fetchCart();
  }, [fetchCart]);

  // Инициализируем скрипт управления фоном при прокрутке
  useEffect(() => {
    // Скрипт уже инициализируется автоматически при импорте
    // Но можем принудительно обновить если нужно
    if (scrollBackgroundToggle && scrollBackgroundToggle.refresh) {
      scrollBackgroundToggle.refresh();
    }
    
    // Cleanup при размонтировании компонента
    return () => {
      if (scrollBackgroundToggle && scrollBackgroundToggle.destroy) {
        scrollBackgroundToggle.destroy();
      }
    };
  }, []);

  // Временно отключаем экран загрузки для отладки скролла
  // if (loading) {
  //   return (
  //     <div className="App">
  //       <div style={{
  //         display: 'flex',
  //         justifyContent: 'center',
  //         alignItems: 'center',
  //         height: '100vh',
  //         fontSize: '18px'
  //       }}>
  //         Загрузка...
  //       </div>
  //     </div>
  //   );
  // }

  return (
    <div className="App">

      <Header isHome={isHome} isBurgerMenuOpen={isBurgerMenuOpen} setIsBurgerMenuOpen={setIsBurgerMenuOpen} />
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
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/collections/:slug" element={<CollectionDetailPage />} />
            <Route path="/account" element={<Account />} />
            <Route path="/addresses" element={<AddressesPage />} />
            <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="/order-confirmation/:orderId" element={<OrderConfirmationPage />} />
            <Route path="/reset-password" element={<PasswordResetConfirm />} />
            <Route path="/auth/google/callback" element={<GoogleOAuthCallback />} />
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