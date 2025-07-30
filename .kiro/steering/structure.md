# Project Structure

## Root Directory Layout

```
├── guscha_django/           # Django backend application
├── guscha_django_frontend/  # React frontend application
├── guscha_project/          # Legacy/additional project files
├── build_frontend_improved.ps1  # Automated build script
└── README.md               # Project documentation
```

## Django Backend Structure (`guscha_django/`)

```
guscha_django/
├── apps/                   # Django applications (modular architecture)
│   ├── accounts/          # User authentication and profiles
│   ├── addresses/         # Address management (shipping/billing)
│   ├── cart/             # Shopping cart functionality
│   ├── core/             # Core utilities and middleware
│   ├── orders/           # Order processing and management
│   └── products/         # Product catalog and management
├── guscha_project/        # Django project settings
│   ├── settings.py       # Main configuration file
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI application
├── templates/            # Django templates (includes React index.html)
├── static/              # Static files for development
├── static_root/         # Collected static files for production
├── media/               # User-uploaded files
├── db.sqlite3           # SQLite database
├── manage.py            # Django management script
└── requirements.txt     # Python dependencies
```

## React Frontend Structure (`guscha_django_frontend/`)

```
guscha_django_frontend/
├── src/
│   ├── api/             # API service layer (axios configurations)
│   ├── components/      # Reusable React components
│   ├── pages/           # Page-level components
│   ├── hooks/           # Custom React hooks
│   ├── store/           # Zustand state management
│   ├── styles/          # CSS and styling files
│   ├── utils/           # Utility functions
│   ├── App.js           # Main application component
│   └── index.js         # Application entry point
├── public/              # Static assets
├── build/               # Production build output
├── package.json         # Node.js dependencies and scripts
└── tailwind.config.js   # Tailwind CSS configuration
```

## Django Apps Architecture

Each Django app follows the standard structure:
- `models.py` - Database models
- `views.py` - API views (ViewSets)
- `serializers.py` - DRF serializers
- `urls.py` - URL patterns
- `admin.py` - Admin interface configuration
- `apps.py` - App configuration

## Key Conventions

### File Naming
- **Django**: Snake_case for Python files and variables
- **React**: PascalCase for components, camelCase for functions/variables
- **URLs**: Kebab-case for API endpoints

### Import Organization
- **Django**: Standard library → Third-party → Local imports
- **React**: React imports → Third-party → Local components → Utilities

### API Structure
- RESTful endpoints following `/api/v1/{app}/{resource}/` pattern
- ViewSets for CRUD operations
- Custom actions for specific business logic

### Component Organization
- **Pages**: Top-level route components
- **Components**: Reusable UI components
- **API**: Service layer for backend communication
- **Store**: Global state management with Zustand

### Static Files Handling
- Development: Separate static directories
- Production: Collected into `static_root/` via `collectstatic`
- React build files integrated into Django static system

### Environment Configuration
- `.env` files for sensitive configuration
- Separate settings for development/production
- Environment-specific API endpoints and keys