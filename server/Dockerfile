# Stage 1: Base build stage
 FROM python:3.13-slim AS builder
 ENV PYTHONDONTWRITEBYTECODE=1
 ENV PYTHONUNBUFFERED 1
 RUN apt-get update && apt-get install -y \
     libpq-dev gcc \
     && rm -rf /var/lib/apt/lists/*

 RUN mkdir /app
 WORKDIR /app
 RUN pip install --upgrade pip 
 COPY requirements.txt  /app/
 RUN pip install --no-cache-dir -r requirements.txt
 COPY . /app/

## CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Stage 2: Production stage
#FROM python:3.13-slim AS builder
 
# RUN useradd -m -r appuser && \
#   mkdir /app && \
#   chown -R appuser /app
 
# Copy the Python dependencies from the builder stage
# COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
# COPY --from=builder /usr/local/bin/ /usr/local/bin/
 
# Set the working directory
# WORKDIR /app
 
# Copy application code
# COPY --chown=appuser:appuser . .
 
# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
 
# Switch to non-root user
# USER appuser
 

