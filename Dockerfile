# Use a lightweight Python base image
FROM python:3.10-slim

# Install system dependencies (tesseract + build tools)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose port for Render
EXPOSE 8000

# Start command (Gunicorn + Django WSGI)
CMD ["gunicorn", "aadhaar_api.wsgi:application", "--bind", "0.0.0.0:8000"]
