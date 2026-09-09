"""URL configuration for the variantdb project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("variants.urls")),
]
