FROM golang:1.20-alpine AS ProxyBuilder

WORKDIR /app
RUN apk add git && git clone https://github.com/acheong08/ChatGPT-Proxy-V4 

WORKDIR /app/ChatGPT-Proxy-V4

RUN CGO_ENABLED=0 go build -a -installsuffix cgo .

FROM node:18-alpine as node
COPY frontend /app/frontend
WORKDIR /app/frontend

RUN npm install && npm run build

FROM python:3.10-alpine

ARG PIP_CACHE_DIR=/pip_cache
ARG TARGETARCH

RUN mkdir -p /app/backend

RUN apk add --update caddy
RUN if [ "${TARGETARCH}" = "arm64" ] ; then \
        apk add --no-cache gcc musl-dev libffi-dev \
    ; fi

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY Caddyfile /app/Caddyfile
COPY backend /app/backend
COPY --from=node /app/frontend/dist /app/dist
COPY --from=ProxyBuilder /app/ChatGPT-Proxy-V4/ChatGPT-Proxy-V4 /app/backend/ChatGPT-Proxy-V4

WORKDIR /app

EXPOSE 80

COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh; mkdir /data
CMD ["/app/startup.sh"]