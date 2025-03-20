from celery import shared_task
from views import poll_events

@shared_task
def poll_events_task():
    provider_id = "api-sports"  # or get from configuration
    poll_events(provider_id)