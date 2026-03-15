"""
DorfinMUD URL configuration.

Extends the default Evennia URL patterns with a Prometheus metrics endpoint.
"""

from django.urls import path

from evennia.web.urls import urlpatterns as evennia_default_urlpatterns

from web.views_metrics import metrics_view

urlpatterns = [
    path("metrics", metrics_view, name="prometheus-metrics"),
] + evennia_default_urlpatterns
