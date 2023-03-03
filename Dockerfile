FROM alpine:latest

RUN mkdir /app
WORKDIR /app

COPY Caddyfile /app/Caddyfile

RUN apk add --update python3 py3-pip
RUN apk add --update nodejs npm
RUN apk add --update caddy
RUN npm install -g pnpm

COPY backend /app/backend
COPY frontend /app/frontend

WORKDIR /app/frontend
RUN pnpm install
RUN pnpm build

WORKDIR /app/backend
RUN pip install -r requirements.txt

WORKDIR /app
RUN cp -r frontend/dist /app
RUN rm -rf frontend

EXPOSE 80

RUN mkdir /data
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh
CMD ["/app/startup.sh"]