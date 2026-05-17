FROM python:3.12-slim

WORKDIR /app

# Install system dependencies + Node.js
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build React frontend
COPY web/ ./web/
WORKDIR /app/web
RUN npm install && npm run build

# Copy rest of the app
WORKDIR /app
COPY . .

# Environment variables
ENV PORT=5050
EXPOSE 5050

CMD ["python", "app.py"]
