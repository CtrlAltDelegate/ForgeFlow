# ForgeFlow API with OpenSCAD for STL export
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install OpenSCAD for STL export (headless; CLI only)
RUN apt-get update && apt-get install -y --no-install-recommends openscad \
    && rm -rf /var/lib/apt/lists/*

# App dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY pyproject.toml .

# Default: OpenSCAD is on PATH after apt install
ENV FORGEFLOW_OPENSCAD_PATH=openscad

EXPOSE 8080
# Use PORT so Railway (and others) can assign the port at runtime
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
