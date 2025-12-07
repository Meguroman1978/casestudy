# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11.11

FROM python:${PYTHON_VERSION}-slim

LABEL fly_launch_runtime="flask"

WORKDIR /code

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Download Template.pptx from Google Slides at build time
# Note: This requires GOOGLE_SLIDES_ID to be set as build arg or will be downloaded at runtime
# For runtime download, see start.sh

EXPOSE 8080

# Use Gunicorn instead of Flask development server
# Download template and start server
CMD python3 download_template_from_slides.py && \
    gunicorn app:app \
    --bind 0.0.0.0:8080 \
    --workers 1 \
    --timeout 300 \
    --worker-class sync \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile -
