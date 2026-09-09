from django.urls import path

from . import views

app_name = "variants"

urlpatterns = [
    path("", views.variant_list, name="variant_list"),
]
