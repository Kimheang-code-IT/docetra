# Docetra frontend — Nuxt 3 (node-server output)
# Build:  docker build -t docetra-frontend:local .
# Run:    docker run -p 3000:3000 -e NUXT_PUBLIC_API_BASE=http://api:8000 docetra-frontend:local
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production HOST=0.0.0.0 PORT=3000
RUN addgroup -S docetra && adduser -S docetra -G docetra
COPY --from=build /app/.output ./.output
USER docetra
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
