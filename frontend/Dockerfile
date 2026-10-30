# QuickTicket web — Vite SPA served by nginx.
# Built with bun (bun.lock); output dist/ copied into a tiny nginx image.
# API calls are same-origin (VITE_API_URL unset at build = ""), routed by
# Traefik: /api/* -> api service, everything else -> this container.
FROM oven/bun:1-alpine AS build
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
