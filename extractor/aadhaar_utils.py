import os
import re
import cv2
import numpy as np
import pytesseract
import datetime
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
import shutil
import platform

# -----------------------
# Robust Tesseract Path Detection
# -----------------------
tesseract_path = shutil.which("tesseract")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
elif platform.system() == "Windows":
    win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(win_path):
        pytesseract.pytesseract.tesseract_cmd = win_path
    else:
        raise EnvironmentError("Tesseract not found at default Windows path")
else:
    linux_path = "/usr/bin/tesseract"
    if os.path.exists(linux_path):
        pytesseract.pytesseract.tesseract_cmd = linux_path
    else:
        raise EnvironmentError("Tesseract not found in PATH or default location")


# -----------------------
# Preprocessing Functions
# -----------------------

def preprocess_aadhaar(img):
    """
    Preprocess Aadhaar image (OpenCV array) for better OCR results.
    Optimized for low memory (Render free tier).
    """
    if isinstance(img, str):  # if file path passed
        img = cv2.imread(img)

    # Convert to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale slightly (not too high)
    gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # Light denoising (Gaussian instead of heavy bilateral)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Sharpening (light kernel)
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, kernel)

    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        31, 15
    )

    return thresh


def extract_text(img):
    """
    Extract raw text from Aadhaar image (OpenCV array or file path).
    """
    if isinstance(img, str):  # file path
        img = cv2.imread(img)

    processed = preprocess_aadhaar(img)

    # Memory-friendly config
    config = r'--oem 1 --psm 6 -l eng'

    text = pytesseract.image_to_string(processed, config=config)
    return text


def extract_aadhaar_details(raw_text: str):
    """
    Extract structured Aadhaar details from OCR raw text.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    details = {
        "Name": "",
        "DOB": "",
        "AadhaarNo": "",
        "Address": "",
        "Mobile": ""
    }

    full_text = " ".join(lines)

    # Aadhaar number
    aadhaar_match = re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", full_text)
    if aadhaar_match:
        details["AadhaarNo"] = aadhaar_match.group(0)

    # DOB
    dob_match = re.search(r"DOB[:\s]+(\d{2}[/-]\d{2}[/-]\d{4}|\d{4})", full_text, re.IGNORECASE)
    if dob_match:
        dob_val = dob_match.group(1)
        if len(dob_val) == 4:  # Only year
            dob_val = f"01/01/{dob_val}"
        dob_val = dob_val.replace("-", "/")
        details["DOB"] = dob_val

    # Mobile
    number_match = re.search(r"\b\d{10}\b", full_text)
    if number_match:
        details["Mobile"] = number_match.group(0)

    # Name & Address
    name = None
    address_lines = []
    for i, line in enumerate(lines):
        if line.startswith(("S/O", "D/O", "C/O")):
            if i > 0:
                name = lines[i - 1]
            j = i
            while j < len(lines):
                if re.search(r"\b\d{10}\b", lines[j]) or re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", lines[j]):
                    break
                address_lines.append(lines[j])
                j += 1
            break

    if name:
        details["Name"] = name
    if address_lines:
        details["Address"] = ", ".join(address_lines)

    return details


# -----------------------
# OOP Aadhaar Processor
# -----------------------

class AadhaarProcessor:
    def __init__(self, aadhaar_folder, person_folder, output_file):
        self.aadhaar_folder = aadhaar_folder
        self.person_folder = person_folder
        self.output_file = output_file

    def extract_text_from_image(self, img_path):
        """Wrapper for OCR text extraction."""
        return extract_text(img_path)

    def parse_adhaar_details(self, text):
        """Wrapper for detail parsing."""
        return extract_aadhaar_details(text)

    def calculate_age(self, dob_str):
        """Calculate age from DOB."""
        try:
            dob = datetime.datetime.strptime(dob_str, "%d/%m/%Y")
            today = datetime.date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except Exception:
            return ""

    def process_pair(self, aadhaar_file, person_file):
        """Process Aadhaar + person image pair."""
        text = self.extract_text_from_image(aadhaar_file)
        details = self.parse_adhaar_details(text)

        # Age
        if details["DOB"]:
            details["Age"] = self.calculate_age(details["DOB"])
        else:
            details["Age"] = ""

        # Extract ID from filename
        base_id = os.path.splitext(os.path.basename(aadhaar_file))[0].split("_")[-1]
        details["ID"] = base_id
        details["AadhaarImage"] = aadhaar_file
        details["PersonImage"] = person_file if person_file else None

        return details
