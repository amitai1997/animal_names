# Use official Python image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt ./
COPY pyproject.toml ./
COPY poetry.lock ./
COPY README.md ./
COPY src ./src

# Install dependencies (prefer poetry if available, fallback to pip)
RUN pip install --upgrade pip && \
    if [ -f pyproject.toml ]; then \
        pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi; \
    else \
        pip install -r requirements.txt; \
    fi

# Copy project files
COPY . .

# Default command (can be overridden)
CMD ["python", "-m", "src.cli", "--output", "report.html"]
