# celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_picks.settings')

app = Celery('campus_picks')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


