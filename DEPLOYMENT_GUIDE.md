# Complete Deployment Guide for Django + React Applications

## Overview
This guide covers the complete deployment process for a Django backend with React frontend, based on lessons learned from deploying the PetReunite project.

## Pre-Deployment Checklist

### 1. Project Structure Verification
```
project-root/
├── Backend/                 # Django project root
│   ├── manage.py
│   ├── requirements.txt     # MUST be lowercase
│   ├── ProjectName/         # Main Django app
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── apps/               # Django apps
├── frontend/               # React project root
│   ├── package.json
│   ├── .env
│   └── src/
└── README.md
```

### 2. Backend (Django) Preparation

#### A. Requirements File
- **File name**: `requirements.txt` (lowercase - Linux servers are case-sensitive)
- **Location**: `Backend/requirements.txt`
- **Essential packages**:
```txt
Django>=5.0.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
django-cors-headers>=4.3.0
Pillow>=10.4.0
channels>=4.0.0
daphne>=4.0.0
dj-database-url>=2.0.0
whitenoise>=6.0.0
gunicorn>=21.0.0
setuptools>=68.0.0
psycopg2-binary>=2.9.0  # For PostgreSQL
```

#### B. Settings Configuration (`Backend/ProjectName/settings.py`)
```python
import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-fallback-secret-key')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Allowed Hosts
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'your-domain.com',
    'your-app.onrender.com',  # Add your deployment domain
    'your-app.vercel.app',
]

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://your-frontend.vercel.app",
]

CORS_ALLOW_CREDENTIALS = True

# Database Configuration
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Middleware (add whitenoise)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

#### C. ASGI Configuration (`Backend/ProjectName/asgi.py`)
```python
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProjectName.settings')
django.setup()  # CRITICAL: Must be before importing models

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing  # Import after django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
```

### 3. Frontend (React) Preparation

#### A. Environment Configuration (`.env`)
```env
# Development
# REACT_APP_API_URL=http://localhost:8000

# Production
REACT_APP_API_URL=https://your-backend.onrender.com
```

#### B. Vercel Configuration (`vercel.json`)
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

#### C. Package.json Build Scripts
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

## Deployment Steps

### Phase 1: Backend Deployment (Render)

#### Step 1: Create Render Account & PostgreSQL Database
1. Sign up at render.com
2. Create new PostgreSQL database
3. Note the database URL (starts with `postgresql://`)

#### Step 2: Create Web Service
1. Connect GitHub repository
2. **Root Directory**: Leave blank (auto-detect) or set to `Backend`
3. **Build Command**: 
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```
4. **Start Command**: 
   ```bash
   gunicorn ProjectName.wsgi:application
   ```

#### Step 3: Environment Variables
Set these in Render dashboard:
```
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

#### Step 4: Generate Secret Key
```python
# Run this in Python shell
import secrets
print(secrets.token_urlsafe(50))
```

### Phase 2: Frontend Deployment (Vercel)

#### Step 1: Create Vercel Account
1. Sign up at vercel.com
2. Connect GitHub repository

#### Step 2: Configure Deployment
1. **Root Directory**: `frontend`
2. **Build Command**: `npm run build`
3. **Output Directory**: `dist`

#### Step 3: Environment Variables
Set in Vercel dashboard:
```
REACT_APP_API_URL=https://your-backend.onrender.com
```

## Common Issues & Solutions

### 1. Requirements.txt Issues
**Problem**: `Requirements.txt` vs `requirements.txt`
**Solution**: Always use lowercase `requirements.txt` for Linux compatibility

### 2. Pillow Build Errors
**Problem**: Pillow version compatibility
**Solution**: Use `Pillow>=10.4.0` and add `setuptools>=68.0.0`

### 3. Missing Dependencies
**Problem**: `ModuleNotFoundError: No module named 'pkg_resources'`
**Solution**: Add `setuptools>=68.0.0` to requirements.txt

### 4. ASGI Import Errors
**Problem**: Models imported before Django setup
**Solution**: Call `django.setup()` before importing any models in asgi.py

### 5. Static Files Not Serving
**Problem**: CSS/JS not loading in production
**Solution**: Add whitenoise middleware and configure STATIC_ROOT

### 6. CORS Issues
**Problem**: Frontend can't connect to backend
**Solution**: Configure CORS_ALLOWED_ORIGINS with frontend URL

### 7. Database Connection Errors
**Problem**: 500 errors on API calls
**Solution**: Set DATABASE_URL environment variable and run migrations

### 8. SPA Routing Issues (Vercel)
**Problem**: 404 on direct URL access
**Solution**: Add vercel.json with rewrites configuration

### 9. TypeScript Build Errors
**Problem**: Missing type declarations
**Solution**: Create missing type files or update imports

## Environment Variables Checklist

### Backend (Render)
- [ ] `SECRET_KEY` - Generated secret key
- [ ] `DEBUG` - Set to `False`
- [ ] `DATABASE_URL` - PostgreSQL connection string

### Frontend (Vercel)
- [ ] `REACT_APP_API_URL` - Backend URL

## Testing Deployment

### Backend Tests
1. Visit `https://your-backend.onrender.com/admin/`
2. Test API endpoints: `https://your-backend.onrender.com/api/`
3. Check logs in Render dashboard

### Frontend Tests
1. Visit deployed URL
2. Test all routes (should not show 404)
3. Test API connections
4. Check browser console for errors

## Git Workflow

### Repository Setup
```bash
# Add personal repo as backup remote
git remote add backup https://github.com/username/repo-name.git

# Push to personal repo
git push backup main --force
```

### Deployment Updates
```bash
# Make changes
git add .
git commit -m "deployment fixes"

# Push to personal repo (triggers auto-deploy)
git push backup main
```

## Security Checklist

- [ ] SECRET_KEY is randomly generated and secure
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured properly
- [ ] CORS origins restricted to your domains
- [ ] Database credentials secured
- [ ] No sensitive data in git repository
- [ ] Environment variables used for all secrets

## Performance Optimization

### Backend
- [ ] Enable gzip compression (whitenoise)
- [ ] Configure static file caching
- [ ] Optimize database queries
- [ ] Use connection pooling

### Frontend
- [ ] Enable build optimization
- [ ] Configure CDN for assets
- [ ] Implement code splitting
- [ ] Optimize images and assets

## Monitoring & Maintenance

### Backend Monitoring
- Monitor Render logs for errors
- Set up database backups
- Monitor API response times
- Track error rates

### Frontend Monitoring
- Monitor Vercel deployment logs
- Check Core Web Vitals
- Monitor JavaScript errors
- Track user experience metrics

## Troubleshooting Commands

### Check Render Logs
```bash
# View recent logs in Render dashboard
# Or use Render CLI if available
```

### Local Testing
```bash
# Test production settings locally
export DEBUG=False
export SECRET_KEY=your-secret-key
python manage.py runserver
```

### Database Operations
```bash
# Run migrations on Render
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Final Deployment Verification

### Checklist
- [ ] Backend API responds correctly
- [ ] Frontend loads without errors
- [ ] Database connections work
- [ ] Authentication functions properly
- [ ] File uploads work (if applicable)
- [ ] WebSocket connections work (if applicable)
- [ ] All environment variables set
- [ ] HTTPS certificates active
- [ ] Custom domains configured (if applicable)

## Next Project Template

For your next project, use this structure from the start:

```
my-next-project/
├── backend/
│   ├── requirements.txt     # lowercase!
│   ├── manage.py
│   ├── .env.example
│   └── myproject/
│       ├── settings.py      # production-ready from start
│       ├── asgi.py         # proper import order
│       └── wsgi.py
├── frontend/
│   ├── .env.example
│   ├── vercel.json         # SPA routing config
│   └── src/
├── .gitignore              # exclude .env files
└── DEPLOYMENT.md           # this guide
```

This comprehensive guide should help you avoid all the deployment issues you encountered and streamline future deployments.