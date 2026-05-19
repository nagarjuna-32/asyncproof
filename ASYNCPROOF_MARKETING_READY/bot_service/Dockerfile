FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "bot_service.bot_service:app", "--host", "0.0.0.0", "--port", "9000"]
