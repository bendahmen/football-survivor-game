# Create this as football_survivor_game/settings_production.py
# This extends your base settings for production

from .settings import *
import dj_database_url
import os

# Security settings for production
DEBUG = False
ALLOWED_HOSTS = [
    '.onrender.com',  # Render.com domains
    'localhost',
    '127.0.0.1',
]

# Add your render app URL when you know it
# ALLOWED_HOSTS.append('your-app-name.onrender.com')

# Database - Render provides DATABASE_URL
# DATABASES = {
#     'default': dj_database_url.config(
#         conn_max_age=600,
#         conn_health_checks=True,
#     )
# }
DATABASES = {
    'default': dj_database_url.parse('postgresql://postgres:F4vyM6wdCrILiDg8@db.qoeheccljivukhgajelq.supabase.co:5432/postgres')
}

# Static files with WhiteNoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Add CSRF trusted origins for Render
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'http://localhost:8000',
]

# Ensure logout redirect works
LOGOUT_REDIRECT_URL = '/'

# API Keys from environment variables
FOOTBALL_DATA_API_KEY = os.environ.get('FOOTBALL_DATA_API_KEY')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}