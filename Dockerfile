FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

ENV PYTHONUNBUFFERED=1
ENV GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true

EXPOSE 8080

CMD ["python3", "-m", "google.adk.cli", "run", "symptom_navigator.agent:root_agent"]
