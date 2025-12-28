"""
WSGI config for Smart Hire project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hire.settings')
application = get_wsgi_application()

