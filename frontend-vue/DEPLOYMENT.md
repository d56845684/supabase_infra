# Frontend Docker Deployment

This guide packages the Vue admin frontend into a static image and serves it with Nginx.

## Build

From the repository root:

```bash
docker build -t teaching-platform-frontend -f frontend-vue/Dockerfile frontend-vue
```

- Uses Node 20 for the build step and Nginx Alpine for the runtime image.
- The build copies only `package.json` first to leverage Docker layer caching for dependencies.
- Requires `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` to point the app at your Supabase gateway.

## Run

Publish the container on your host (the app is served on port 80 inside the container):

```bash
docker run -d \
  --name teaching-platform-frontend \
  -p 4173:80 \
  teaching-platform-frontend
```

Adjust the host port (`4173` above) as needed. The Nginx configuration includes a history mode fallback for Vue Router.

## Compose

To run the Supabase stack and the Vue frontend together, use the bundled compose service:

```bash
# ensure .env contains SUPABASE_PUBLIC_URL, ANON_KEY, and FRONTEND_PORT (optional)
docker compose up --build frontend
```

- The compose service builds the SPA using the Supabase endpoint from `SUPABASE_PUBLIC_URL` and injects the anonymous key from `ANON_KEY`.
- `FRONTEND_PORT` controls the host port (defaults to `4173`).

## Updating

1. Pull the latest code.
2. Rebuild the image with the same tag (e.g., `teaching-platform-frontend`).
3. Restart the container:

```bash
docker stop teaching-platform-frontend && docker rm teaching-platform-frontend
docker run -d --name teaching-platform-frontend -p 4173:80 teaching-platform-frontend
```

## Integrating behind a reverse proxy

If you terminate TLS elsewhere, place this container behind your reverse proxy (e.g., Nginx, Traefik, Caddy) and forward traffic to the exposed port. The included Nginx config caches static assets and keeps SPA routing intact.
