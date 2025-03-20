from django.urls import path
from .views import trigger_polling

urlpatterns = [
    path('polling/', trigger_polling, name='trigger_polling'),
    # ... other endpoints
]
