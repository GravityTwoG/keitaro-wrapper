FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package.json
COPY e2e/package.json e2e/package.json

RUN npm ci --ignore-scripts

COPY frontend ./frontend

RUN npm --prefix frontend run build

FROM nginx:1.29-alpine AS runtime

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 80
