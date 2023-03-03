#!/bin/sh
cd /app
caddy start --config /app/Caddyfile --adapter caddyfile
cd /app/backend
python main.py