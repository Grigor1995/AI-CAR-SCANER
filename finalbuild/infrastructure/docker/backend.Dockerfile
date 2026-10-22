FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY vehicle vehicle
COPY data data
COPY assets/vehicle_models assets/vehicle_models
ENV PYTHONPATH=/app:/app/backend
CMD ["uvicorn","api.main:app","--host","0.0.0.0","--port","8000"]
