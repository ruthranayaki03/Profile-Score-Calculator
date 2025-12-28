# SmartHire Django Application
# Automated Interview Platform with ML-based Personality Prediction

try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed, running without async tasks
    celery_app = None
    __all__ = ()

