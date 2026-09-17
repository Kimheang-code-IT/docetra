# Docetra frontend — static SPA, served by the nginx edge container.
# Build:  docker build -t docetra-frontend:local .
# Runtime is nginx with the compiled files baked in at /usr/share/nginx/html;
# nginx (infrastructure/nginx/docker.conf) proxies /api/ to FastAPI.
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
# Static SPA output — no Nitro/Node runtime, no SSR server process.
ENV NUXT_STATIC_SPA=true
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Public values are baked at build time (import.meta.env). Leave API base empty
# for same-origin `/api/v2`; set NUXT_PUBLIC_SITE_URL for OG/Twitter previews.
ARG NUXT_PUBLIC_SITE_URL=
ENV NUXT_PUBLIC_SITE_URL=${NUXT_PUBLIC_SITE_URL}
RUN pnpm generate

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/.output/public /usr/share/nginx/html
EXPOSE 80
