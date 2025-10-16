"""
Configuración para desarrollo.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Hosts permitidos en desarrollo
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

# CORS settings para desarrollo
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Database para desarrollo (usa los valores por defecto de base.py)

# Cache en desarrollo (Redis local o Docker)
import os
if os.environ.get('REDIS_HOST'):
    # Corriendo en Docker
    CACHES['default']['LOCATION'] = f'redis://{os.environ.get("REDIS_HOST", "redis")}:6379/1'
else:
    # Corriendo localmente
    CACHES['default']['LOCATION'] = 'redis://localhost:6379/1'

# Configuración adicional para desarrollo
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar (si está instalado)
if 'debug_toolbar' in INSTALLED_APPS:
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1', 'localhost']