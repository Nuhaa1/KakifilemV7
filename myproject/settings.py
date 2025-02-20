from pathlib import Path
import os
import sys
from dotenv import load_dotenv
import dj_database_url

# Load environment variables first
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key-here'
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Get Railway-provided URL and ensure it has proper scheme
RAILWAY_URL = os.environ.get('RAILWAY_STATIC_URL', '')
if RAILWAY_URL and not RAILWAY_URL.startswith(('http://', 'https://')):
    RAILWAY_URL = f'https://{RAILWAY_URL}'

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

# Add Railway URL to CSRF_TRUSTED_ORIGINS if available
if RAILWAY_URL:
    CSRF_TRUSTED_ORIGINS.extend([
        RAILWAY_URL,
        RAILWAY_URL.replace('https://', 'http://')
    ])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'videoapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Make sure this is second
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'
WSGI_APPLICATION = 'myproject.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database configuration
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('PGDATABASE'),
            'USER': os.environ.get('PGUSER'),
            'PASSWORD': os.environ.get('PGPASSWORD'),
            'HOST': os.environ.get('PGHOST'),
            'PORT': os.environ.get('PGPORT'),
        }
    }
else:
    # Use DATABASE_URL from Railway with fallback
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        DATABASES = {
            'default': dj_database_url.parse(database_url, conn_max_age=600)
        }
    else:
        # Fallback to local database if no DATABASE_URL is set
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('PGDATABASE', 'Kakifilem'),
                'USER': os.environ.get('PGUSER', 'postgres'),
                'PASSWORD': os.environ.get('PGPASSWORD', 'Amanfiy77'),
                'HOST': os.environ.get('PGHOST', 'localhost'),
                'PORT': os.environ.get('PGPORT', '5432'),
            }
        }

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Use basic static files storage during development
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add the bot directory to Python path
sys.path.append(os.path.join(BASE_DIR, 'videoapp/bot'))

# Get port from environment variable
PORT = os.environ.get('PORT', '8000')

# Site URL settings for Railway
if DEBUG:
    SITE_URL = f'http://127.0.0.1:{PORT}'
else:
    if RAILWAY_URL:
        SITE_URL = RAILWAY_URL
    else:
        SITE_URL = f'http://127.0.0.1:{PORT}'

# Force HTTPS in production
if not DEBUG and not SITE_URL.startswith('https://'):
    SITE_URL = SITE_URL.replace('http://', 'https://', 1)

# Telegram Bot Settings
TELEGRAM_API_ID = os.environ.get('API_ID')
TELEGRAM_API_HASH = os.environ.get('API_HASH')
TELEGRAM_BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Set defaults for development only
if DEBUG:
    SITE_URL = SITE_URL or 'http://127.0.0.1:8000'
    
    # Warning: These are dummy values for development
    if not TELEGRAM_API_ID:
        TELEGRAM_API_ID = '123456'
    if not TELEGRAM_API_HASH:
        TELEGRAM_API_HASH = 'dummy_hash'
    if not TELEGRAM_BOT_TOKEN:
        TELEGRAM_BOT_TOKEN = 'dummy_token'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
