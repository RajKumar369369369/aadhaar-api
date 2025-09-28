import os
import tempfile
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .aadhaar_utils import extract_text, extract_aadhaar_details

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def extract_aadhaar(request):
    """
    Accept Aadhaar image upload, extract text using OCR,
    and return structured JSON details.
    """
    if 'file' not in request.FILES:
        return Response({"error": "No file uploaded. Please upload an Aadhaar image."}, status=400)

    file_obj = request.FILES['file']

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        for chunk in file_obj.chunks():
            tmp_file.write(chunk)
        tmp_path = tmp_file.name

    try:
        # Run OCR + parsing
        raw_text = extract_text(tmp_path)
        details = extract_aadhaar_details(raw_text)

        # Return structured JSON
        return Response(details)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
