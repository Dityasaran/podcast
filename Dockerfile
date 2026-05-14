FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (e.g., ffmpeg for pydub/audio processing)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables
ENV PORT=5050
EXPOSE 5050

CMD ["python", "app.py"]
