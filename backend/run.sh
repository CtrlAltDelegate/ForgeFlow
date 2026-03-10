#!/bin/sh
# Use PORT from environment (Railway, etc.) or default 8080
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
