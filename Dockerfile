ARG PIP_CACHE_DIR=/pip_cache

FROM python:3.10-alpine

RUN mkdir -p /app/backend

RUN apk add --update caddy

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --cache-dir=${PIP_CACHE_DIR} -r /tmp/requirements.txt

COPY Caddyfile /app/Caddyfile
COPY backend /app/backend
COPY frontend/dist /app/dist

WORKDIR /app

EXPOSE 80

COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh; mkdir /data
CMD ["/app/startup.sh"]