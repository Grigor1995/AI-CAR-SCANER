FROM python:3.13-slim
WORKDIR /app/finalbuild
COPY finalbuild/backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY finalbuild/backend backend
COPY finalbuild/shared shared
COPY finalbuild/config config
COPY config /app/config
COPY finalbuild/data data
COPY finalbuild/assets/vehicle_models assets/vehicle_models
ENV PYTHONPATH=/app/finalbuild:/app/finalbuild/backend
CMD ["python","-m","backend.main","--migrate","--host","0.0.0.0","--port","8000"]
