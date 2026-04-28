from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("compress/small-pdf", views.compress_small_pdf),
    path("compress/larger-pdf", views.compress_large_pdf),
]
