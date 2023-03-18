FROM python:3.10-slim-buster

ARG PIP_CACHE_DIR=/pip_cache

RUN mkdir -p /app/backend

RUN apt update && apt-get install -y curl
RUN apt install -y debian-keyring debian-archive-keyring apt-transport-https && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list && \
    apt update && apt install caddy


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
