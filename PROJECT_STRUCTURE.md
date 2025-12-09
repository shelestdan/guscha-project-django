# Project Structure and Dependency Map

## Backend (Django, `guscha_django`)
- **Entry points**: `manage.py` boots with `DJANGO_SETTINGS_MODULE=guscha_project.settings`; `guscha_project/urls.py` wires healthcheck, robots, admin, API namespaces, QR trigger, and React catch‑all.
- **Settings**: `guscha_project/settings.py` loads `.env`, switches middleware by mode (`test`/`DEBUG`/prod), configures JWT, Redis cache, Postgres, static/media roots, and registers project apps (`apps.*`, `telegram_bot`). Uses `guardian`, `simple_history`, `cachalot`, `silk` (debug), `allauth`/`dj_rest_auth`, `defender` (commented), CSP.
- **Apps**:
  - `apps.accounts`: custom `User` model + managers, Telegram verification flow (`TelegramVerificationCode`, `PendingUserRegistration`), QR/phone-change/password reset endpoints via `urls.py` + DRF `DefaultRouter` for `UserViewSet`. Depends on `simple_history`, DRF JWT, allauth/dj-rest-auth.
  - `apps.products`: catalog entities (`Category`, `Product`, sizes/colors/variants/images, `ProductReview`, `Wishlist`, `Preorder` etc.), image validators/utils, admin AJAX endpoints for images. `urls.py` exposes DRF viewsets (`categories`, `products`, `preorders`, `wishlist`) and image admin endpoints.
  - `apps.cart`: `CartItem`, `Reservation` with cross-links to `products` (`Product`, `ProductSize`, `Preorder*`) and `accounts.User`; API endpoints in `views.py` (not reviewed) likely hit by frontend cart API.
  - `apps.orders`: `Order`, `OrderItem` referencing `accounts.User`, `products`, `cart.Reservation`, `addresses.Address`. `urls.py` registers DRF viewsets `orders`/`order-items`.
  - `apps.addresses`, `apps.collections`, `apps.background_content`, `apps.core` (admin dashboards, middleware, security utilities, validation), `apps.backup_system` (db backups), `apps.core.urls` also serves admin analytics endpoints.
  - `telegram_bot`: standalone app with `bot.py`, handlers, services, repositories, and `urls.py` (for bot webhooks/admin?).
- **Templates/static**: `templates/` for admin/registration/security; `static/`, `nginx/static/`, `static_root/` hold built assets (likely should be build outputs not versioned).
- **Configs**: `docker-compose.dev.yml`, `Dockerfile`, `Dockerfile.telegram`, `config/nginx.conf`, `config/postgresql.conf`.
- **Data/Backups**: `backups/`, `db_dump.sql`, `media/` uploads, `profiles/` perf profiles, `logs/security.log`.
- **Tests**: scattered (`apps/*/tests.py`, `apps/accounts/tests`, `tests/test_telegram_login_flow.py`).

### Backend dependency highlights
- `settings.py` → loads all `apps.*`, `telegram_bot`; DRF auth via JWT + Token + Session. CSP middleware only in prod branch.
- URLs: root router delegates to each app namespace; React catch‑all ensures SPA routing.
- Cross-model links: `orders` and `cart` depend on `products` and `accounts`; `addresses.Address` required by `orders`; `Wishlist`/`ProductReview` depend on `accounts.User`.
- Security: custom middleware in `apps.core.middleware` for security headers/audit; some rate limit middleware commented out; `defender` middleware disabled.

### Potential backend cleanup candidates
- Versioned build artifacts in `static_root/` and `nginx/static/` usually should be generated at deploy time, not stored in VCS.
- Duplicate `asset-manifest.json` (root/static/asset-manifest.json and `guscha_django/static/asset-manifest.json`) may be stale.
- Artifact folder `C/Program Files/Git/...` under `guscha_django/` looks accidental and should be removed.
- Multiple `default-*.sqlite3` inside `media/` are likely temp databases; move outside repo or gitignore.

## Frontend (React, `guscha_django_frontend`)
- **Entry**: `src/index.js` renders `<App/>`.
- **Routing**: `src/App.js` uses `react-router-dom`; lazy routes for `Account`, product/preorder detail, checkout, order confirmation, addresses, collections, password reset confirm, Google OAuth callback. Global layout: `Header`, `Footer`, `CartSidebar`, `ToastContainer`.
- **State (Zustand)**:
  - `store/cartStore.js` — persists cart, calls `cartApi` for CRUD/reservations, toggles UI.
  - `store/productsStore.js` — fetches product lists via `productsApi`.
  - `store/userStore.js` — auth/session (login/register/refresh/profile/logout/googleLogin, csrf fetch) via `authApi`.
- **API layer**: `src/api/axiosInstance.js` sets `baseURL` from `REACT_APP_API_URL` or `window.location.origin`, attaches JWT from `localStorage`, CSRF cookie, cart session header, toast errors. `src/api/index.js` re-exports domain APIs (auth/profile/products/search/reviews/cart/orders/wishlist/preorders/notifications/contact/settings); notes `orderApi.js`/`userApi.js` deprecated.
- **UI/Features**: Components under `components/*` (account flows, security, product forms, video, UI primitives, layouts). Pages under `pages/*`. Global styles under `styles/*`, plus assets (SVG, PNG, OTF).
- **Tests**: `App.test.js`, API tests (cart/products/orders/profile), store tests, component/page tests in `tests/`, hooks tests.

### Frontend dependency highlights
- Network: axios instance targets backend routes `/api/*` matching Django namespaces (`products`, `accounts`, `cart`, `orders`, `addresses`, `collections`, `background`).
- Auth: JWT tokens stored in `localStorage`; CSRF expected from Django cookie; toast errors suppressed for cart and register endpoints.
- Cart: relies on header `X-Session-ID` (matches backend cart session handling).
- Lazy pages depend on corresponding API modules for data fetch; scroll behavior handled via `utils/scrollBackgroundToggle`.

### Potential frontend cleanup candidates
- Duplicate font `Tovar.otf` present both at repo root and `public/fonts/`; keep single source.
- Review `public/` and `src/assets/` for unused images/SVGs; many may be legacy.
- Confirm deprecated API files `orderApi.js`, `userApi.js` (mentioned in `api/index.js`) — if unused, remove to avoid confusion.

## Cross-cutting notes
- Ensure `.env` provides required secrets (`SECRET_KEY`, `JWT_SECRET_KEY`, DB/Redis credentials, TELEGRAM tokens, Google OAuth).
- Consider enabling/adjusting security middleware (`defender`, rate limits) for production once dependencies resolve.
- Validate that generated static assets are excluded from VCS; keep build step in CI/CD.

## Recommended testing (after code changes)
- Backend: `cd guscha_django && python manage.py test` (or targeted app tests).
- Frontend: `cd guscha_django_frontend && npm test` plus `npm run lint` if configured.
- End-to-end: smoke routes `/health`, `/api/products/`, `/api/accounts/`, SPA navigation.

## Quick file map (non-exhaustive but actionable)
- Backend configs: `guscha_django/guscha_project/settings.py`, `urls.py`, `wsgi.py`, `asgi.py`.
- Core apps: `apps/accounts/*`, `apps/products/*`, `apps/cart/*`, `apps/orders/*`, `apps/addresses/*`, `apps/core/*`, `apps/background_content/*`, `apps/backup_system/*`, `telegram_bot/*`.
- Frontend core: `src/App.js`, `src/api/*`, `src/store/*`, `src/components/*`, `src/pages/*`, `src/utils/*`, `src/styles/*`.

