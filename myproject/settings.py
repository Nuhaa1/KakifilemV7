from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key-here'
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [os.getenv('RAILWAY_STATIC_URL', 'https://*.railway.app')]

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

# Site URL settings - ensure it has proper scheme
SITE_URL = os.environ.get('RAILWAY_STATIC_URL', 'http://127.0.0.1:8000')
if not SITE_URL.startswith(('http://', 'https://')):
    SITE_URL = f'https://{SITE_URL}'

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
