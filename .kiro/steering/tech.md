# Technology Stack

## Backend (Django)

- **Framework**: Django 5.2.4 with Django REST Framework 3.15.1
- **Database**: SQLite3 (development), easily configurable for PostgreSQL/MySQL
- **Authentication**: Custom User model with email-based auth, django-allauth integration
- **Security**: django-guardian, django-ratelimit, django-recaptcha, CORS middleware
- **Admin UI**: Jazzmin theme with django-admin-datta
- **Additional**: Pillow for image handling, python-slugify, redis/celery support

## Frontend (React)

- **Framework**: React 19.1.0 with TypeScript support
- **Styling**: Tailwind CSS 3.3.5 with Material-UI components
- **State Management**: Zustand 5.0.5
- **HTTP Client**: Axios 1.9.0 with custom configuration
- **Routing**: React Router DOM 7.6.2
- **Maps**: Google Maps API integration (@react-google-maps/api)
- **UI Components**: Material-UI, React Icons, React Toastify
- **Build Tool**: Create React App with custom build scripts

## Development Environment

- **Platform**: Windows with PowerShell/CMD support
- **Package Managers**: pip (Python), npm (Node.js)
- **Environment**: .env files for configuration
- **Proxy**: Frontend proxies to Django backend (localhost:8000)

## Common Commands

### Backend Setup
```bash
cd guscha_django
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup
```bash
cd guscha_django_frontend
npm install
npm start
```

### Build & Deploy
```powershell
# Automated build script
.\build_frontend_improved.ps1

# Manual steps
cd guscha_django_frontend
npm run build
cd ..\guscha_django
python manage.py collectstatic --noinput
```

### Database Operations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Build Process

The project uses a custom PowerShell script (`build_frontend_improved.ps1`) that:
1. Builds React app with `npm run build`
2. Copies static files to Django's static directory
3. Updates index.html with Django template tags
4. Preserves custom configuration files (axiosConfig.js)

## Environment Configuration

- **Backend**: Uses python-dotenv for .env file support
- **Frontend**: React environment variables with REACT_APP_ prefix
- **Google Maps**: Requires REACT_APP_GOOGLE_MAPS_API_KEY
- **Security**: Configurable DEBUG, SECRET_KEY, RECAPTCHA keys