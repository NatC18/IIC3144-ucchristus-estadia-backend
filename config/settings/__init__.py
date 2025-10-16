"""
Configuración del proyecto UC Christus.

Importa la configuración según el entorno.
"""

import os

# Determinar el entorno
ENVIRONMENT = os.getenv('DJANGO_ENVIRONMENT', 'development').lower()

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .production import *
    DEBUG = True
else:
    from .development import *