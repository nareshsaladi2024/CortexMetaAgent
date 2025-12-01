# Unified Dockerfile for all CortexMetaAgent agents
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy root requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install agent-specific requirements
RUN for dir in agents/AutoEvalAgent agents/MetricsAgent agents/ReasoningCostAgent; do \
    if [ -f "$dir/requirements.txt" ]; then \
        pip install --no-cache-dir -r "$dir/requirements.txt"; \
    fi; \
    done

# Copy all agent directories and workflow
COPY agents/ ./agents/
COPY workflow/ ./workflow/
COPY config.py ./

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_CLOUD_PROJECT=aiagent-capstoneproject
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV ADK_LOG_LEVEL=DEBUG

# Expose port for ADK web interface (if needed)
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "-c", "print('CortexMetaAgent container ready. Use docker-compose to run specific agents.')"]



