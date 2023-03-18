ARG PIP_CACHE_DIR=/pip_cache

FROM golang:1.20.2-alpine AS build

WORKDIR /app

COPY ChatGPT-Proxy-V4 /app/ChatGPT-Proxy-V4
RUN cd /app/ChatGPT-Proxy-V4 && go build

FROM python:3.10-alpine

RUN mkdir -p /app/backend

RUN apk add --update caddy

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --cache-dir=${PIP_CACHE_DIR} -r /tmp/requirements.txt

COPY Caddyfile /app/Caddyfile
COPY backend /app/backend
COPY frontend/dist /app/dist
COPY /app/ChatGPT-Proxy-V4/ChatGPT-Proxy-V4 /app/backend/ChatGPT-Proxy-V4

WORKDIR /app

EXPOSE 80

COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh; mkdir /data
CMD ["/app/startup.sh"]