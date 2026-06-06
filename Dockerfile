FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn requests google-auth reportlab google-cloud-aiplatform google-cloud-storage pillow

COPY main.py /app/main.py

ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
