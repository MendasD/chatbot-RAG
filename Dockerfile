# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app:/app/noxa_app/base:/app/src"
ENV PORT 8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files for production
RUN python noxa_app/base/manage.py collectstatic --noinput || true

# Port is provided by Railway env var
EXPOSE ${PORT}

# Run migrations and start the application using gunicorn
# Note: HF_TOKEN and PINECONE_API_KEY should be set in Railway environment variables
CMD python noxa_app/base/manage.py makemigrations && \
    python noxa_app/base/manage.py migrate && \
    gunicorn --bind 0.0.0.0:${PORT} --chdir /app/noxa_app/base noxa.wsgi:application
