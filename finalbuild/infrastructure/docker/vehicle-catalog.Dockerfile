FROM python:3.13-slim
WORKDIR /app/finalbuild
COPY finalbuild/backend/services/vehicle_catalog/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY finalbuild/backend/services backend/services
COPY finalbuild/backend/configuration backend/configuration
COPY finalbuild/backend/vehicle/__init__.py backend/vehicle/__init__.py
COPY finalbuild/backend/vehicle/interfaces.py backend/vehicle/interfaces.py
COPY finalbuild/backend/vehicle/catalog_registry.py backend/vehicle/catalog_registry.py
COPY finalbuild/backend/vehicle/protocol backend/vehicle/protocol
COPY finalbuild/backend/vehicle/can/__init__.py backend/vehicle/can/__init__.py
COPY finalbuild/backend/vehicle/can/models.py backend/vehicle/can/models.py
COPY finalbuild/data/vehicle_catalog.json data/vehicle_catalog.json
COPY finalbuild/data/vehicle_fitments.json data/vehicle_fitments.json
COPY config /app/config
ENV PYTHONPATH=/app/finalbuild:/app/finalbuild/backend
CMD ["python", "-m", "backend.services.vehicle_catalog", "--host", "0.0.0.0", "--port", "8011"]
