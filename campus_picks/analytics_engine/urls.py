# app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("metrics-dashboard/", views.metrics_dashboard_view, name="metrics_dashboard"),
    path("list-endpoint-metrics/", views.check_metrics, name="metrics_dashboard"),
    path("metrics/", views.log_api_metrics, name="metrics"),
    path("runDailyAnalytics/", views.triggerDailyAnalytics, name="analytics"),
]


