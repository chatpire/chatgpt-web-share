FROM python:3.10-alpine

ARG PIP_CACHE_DIR=/pip_cache

RUN mkdir -p /app/backend

RUN apk add --update caddy
RUN wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub \
    wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.35-r0/glibc-2.35-r0.apk \
    apk add glibc-2.35-r0.apk

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