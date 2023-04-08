FROM golang:1.20-alpine AS ProxyBuilder

COPY ChatGPT-Proxy-V4 /app/ChatGPT-Proxy-V4

WORKDIR /app/ChatGPT-Proxy-V4

RUN CGO_ENABLED=0 go build -a -installsuffix cgo .

FROM python:3.10-alpine

ARG PIP_CACHE_DIR=/pip_cache
ARG BUILDARCH

RUN mkdir -p /app/backend

RUN apk add --update caddy
RUN if [ "${BUILDARCH}" = "arm64" ] ; then \
        apk add --no-cache gcc musl-dev libffi-dev \
    ; fi

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY Caddyfile /app/Caddyfile
COPY backend /app/backend
COPY frontend/dist /app/dist
COPY --from=ProxyBuilder /app/ChatGPT-Proxy-V4/ChatGPT-Proxy-V4 /app/backend/ChatGPT-Proxy-V4

WORKDIR /app

EXPOSE 80

COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh; mkdir /data
CMD ["/app/startup.sh"]