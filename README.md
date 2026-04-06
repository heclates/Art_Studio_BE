## Deploy DRF Backend to Render

This backend is ready for Render deployment with:

- `gunicorn` app server
- `whitenoise` static file serving
- `DATABASE_URL` support
- health check endpoint at `/healthz/`

### 1. Create services on Render

1. Push this repository to GitHub.
2. In Render, create a new Blueprint and point it to the repo root.
3. Render will detect `render.yaml` from the repository root.

### 2. Required environment variables

Set these in Render (or verify values from `render.yaml`):

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DATABASE_URL` (from Render Postgres service)
- `ALLOWED_HOSTS` (include your Render backend domain)
- `FRONTEND_BASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`

Use `backend/.env.example` as the full reference.

### 3. Build and start

Configured in `render.yaml`:

- Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`

### 4. Health checks

- `GET /healthz/`
- `GET /api/health/`

Both return JSON: `{ "status": "ok" }`.
