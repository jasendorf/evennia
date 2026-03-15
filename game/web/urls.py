"""
DorfinMUD URL configuration.

Extends the default Evennia game template URL patterns with a Prometheus
metrics endpoint. Must include the standard website, webclient, and admin
sub-apps — those are NOT part of evennia.web.urls (admin is disabled there).
"""

from django.urls import include, path

from evennia.web.urls import urlpatterns as evennia_default_urlpatterns

from web.views_metrics import metrics_view

urlpatterns = [
    # Prometheus metrics (cluster-internal scraping)
    path("metrics", metrics_view, name="prometheus-metrics"),
    # Standard game template sub-apps
    path("", include("web.website.urls")),
    path("webclient/", include("web.webclient.urls")),
    path("admin/", include("web.admin.urls")),
] + evennia_default_urlpatterns
