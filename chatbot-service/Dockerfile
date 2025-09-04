FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY chatbot_service.py /app/chatbot_service.py

ENV SERVICE_PORT=8085
EXPOSE 8085

CMD ["uvicorn", "chatbot_service:app", "--host", "0.0.0.0", "--port", "8085"]