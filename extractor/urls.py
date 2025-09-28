from django.urls import path
from .views import extract_aadhaar, check_tesseract

urlpatterns = [
    path("extract-aadhaar/", extract_aadhaar, name="extract_aadhaar"),
    path("check-tesseract/", check_tesseract, name="check_tesseract"),
]


