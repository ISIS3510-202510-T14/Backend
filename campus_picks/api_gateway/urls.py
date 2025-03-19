# api/urls.py
from django.urls import path
from .views import location_update_view

urlpatterns = [
    path('location', location_update_view, name='location_update'),
]
