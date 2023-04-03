#!/bin/sh
cd /app
caddy start --config /app/Caddyfile --adapter caddyfile
cd /app/backend
# python main.py
exec uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*' --log-config logging_config.yaml