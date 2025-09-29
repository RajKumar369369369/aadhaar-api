import numpy as np
import cv2
import pytesseract
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
#from .aadhaar_utils import extract_text, extract_aadhaar_details
from .aadhaar_utils import AadhaarProcessor, extract_text, extract_aadhaar_details


def check_tesseract(request):
    """
    Simple endpoint to check if Tesseract OCR is installed and working.
    """
    try:
        version = pytesseract.get_tesseract_version()
        return JsonResponse({"tesseract_version": str(version)})
    except Exception as e:
        return JsonResponse({"error": str(e)})


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def extract_aadhaar(request):
    """
    Accept Aadhaar image upload, extract text using OCR,
    and return structured JSON details.
    """
    if 'file' not in request.FILES:
        return Response(
            {"error": "No file uploaded. Please upload an Aadhaar image."},
            status=400
        )

    file_obj = request.FILES['file']

    try:
        # ✅ Read image directly from memory
        file_bytes = np.frombuffer(file_obj.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img is None:
            return Response({"error": "Could not decode image"}, status=400)

        # ✅ OCR + parsing
        raw_text = extract_text(img)  # <-- extract_text must accept img array
        details = extract_aadhaar_details(raw_text)

        return Response(details)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
