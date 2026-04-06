# Render Environment Variables (copy/paste)

Use these values for web service `art-studio-backend`.

## Required

DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generate-strong-random-string>
DATABASE_URL=<paste-from-render-postgres-or-external-postgres>
ALLOWED_HOSTS=127.0.0.1,localhost,art-studio-backend.onrender.com
FRONTEND_BASE_URL=https://feathure.d374ersqg5p6cr.amplifyapp.com
CORS_ALLOWED_ORIGINS=https://feathure.d374ersqg5p6cr.amplifyapp.com
CSRF_TRUSTED_ORIGINS=https://feathure.d374ersqg5p6cr.amplifyapp.com

## Recommended

DB_CONN_MAX_AGE=600
DB_SSL_REQUIRE=True
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7
DJANGO_LOG_LEVEL=INFO
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

## Optional (email)

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.eu-north-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<smtp_user>
EMAIL_HOST_PASSWORD=<smtp_password>
DEFAULT_FROM_EMAIL=no-reply@aleksandrova-art-studio.cz

## Optional (Supabase sync)

SUPABASE_URL=<https://your-project.supabase.co>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>

## Health check

Set Render health check path to:
/healthz/
