# Frontend Docker Deployment

This guide packages the Vue admin frontend into a static image and serves it with Nginx.

## Build

From the repository root:

```bash
docker build -t teaching-platform-frontend -f frontend-vue/Dockerfile frontend-vue
```

- Uses Node 20 for the build step and Nginx Alpine for the runtime image.
- The build copies only `package.json` first to leverage Docker layer caching for dependencies.

## Run

Publish the container on your host (the app is served on port 80 inside the container):

```bash
docker run -d \
  --name teaching-platform-frontend \
  -p 4173:80 \
  teaching-platform-frontend
```

Adjust the host port (`4173` above) as needed. The Nginx configuration includes a history mode fallback for Vue Router.

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
