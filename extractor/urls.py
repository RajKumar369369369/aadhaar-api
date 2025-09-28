from django.urls import path
from .views import extract_aadhaar

urlpatterns = [
    path('extract-aadhaar/', extract_aadhaar, name='extract_aadhaar'),
]
