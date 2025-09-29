FROM python:3.10-slim

# Install system dependencies + Tesseract OCR + OpenCV libs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    gcc \
    g++ \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Verify tesseract installation (will show in build logs)
RUN which tesseract && tesseract --version

# Set tessdata path (important for pytesseract)
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose Django/Gunicorn port
EXPOSE 8000

# Run with Gunicorn (optimized for Render free tier)
# 1 worker (saves memory), 2 threads, longer timeout
CMD ["gunicorn", "aadhaar_api.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--threads", "2", \
     "--timeout", "120"]
