FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY shared shared
COPY config config
COPY data data
COPY assets/vehicle_models assets/vehicle_models
ENV PYTHONPATH=/app:/app/backend
CMD ["python","-m","backend.main","--migrate","--host","0.0.0.0","--port","8000"]
