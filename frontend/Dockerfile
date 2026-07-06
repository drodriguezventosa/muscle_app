# syntax=docker/dockerfile:1

# ---- Base: install dependencies once ----
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# ---- Dev: Vite dev server with hot-reload (used by docker-compose.override) ----
FROM base AS dev
COPY . .
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---- Build stage: produce static assets ----
FROM base AS builder
COPY . .
RUN npm run build

# ---- Runtime: static files served by nginx ----
FROM nginx:1.27-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
