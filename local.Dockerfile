FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development

WORKDIR /app

# Install system dependencies + Poetry
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    postgresql-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip  \
    && pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy project
COPY . .

# Create directories
RUN mkdir -p /app/staticfiles /app/media

# Collect static files
RUN python AssignMate/manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "AssignMate/manage.py", "runserver", "0.0.0.0:8000"]