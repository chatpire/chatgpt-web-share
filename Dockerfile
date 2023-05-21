FROM node:18-alpine AS FrontendBuilder

RUN mkdir -p /app
COPY frontend /app/frontend

WORKDIR /app/frontend
RUN npm install pnpm -g
RUN pnpm install
RUN pnpm build

FROM python:3.10-alpine

ARG PIP_CACHE_DIR=/pip_cache
ARG TARGETARCH

RUN mkdir -p /app/backend

RUN apk add --update caddy gcc musl-dev libffi-dev

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY Caddyfile /app/Caddyfile
COPY backend /app/backend
COPY --from=FrontendBuilder /app/frontend/dist /app/dist

WORKDIR /app

EXPOSE 80

COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh; mkdir /data
CMD ["/app/startup.sh"]
