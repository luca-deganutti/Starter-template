# Backend Starter Template

Starter profesional para APIs backend con FastAPI, SQLAlchemy 2, Alembic y autenticacion JWT con refresh tokens rotativos y revocables.

## Incluye
- FastAPI con app factory, CORS, logging y `request_id`
- SQLAlchemy 2 + Alembic
- Auth con registro, login, `me`, refresh rotation, logout y cambio de password
- Usuarios con roles (`admin`, `user`)
- Health y readiness checks
- Observabilidad con Prometheus (`/metrics`) y Sentry
- Configuracion por entorno con validaciones
- Pytest, Ruff, Black, MyPy y pre-commit
- Docker, Docker Compose y CI para GitHub Actions

## Requisitos
- Python 3.12
- PostgreSQL 16 o Docker

## Estructura
```text
app/
  api/v1/
  core/
  db/
  models/
  repositories/
  schemas/
  services/
alembic/
tests/
```

## Setup local
```bash
mkvenv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Variables clave
- `SGI_ENV`: `dev`, `test` o `prod`
- `SGI_DATABASE_URL`: cadena de conexion SQLAlchemy
- `SGI_JWT_SECRET_KEY`: secreto JWT, obligatorio fuerte en `prod`
- `SGI_ALLOW_OPEN_REGISTRATION`: habilita o no `/auth/register`
- `SGI_AUTO_PROMOTE_FIRST_USER_TO_ADMIN`: solo recomendable en `dev`
- `SGI_INITIAL_ADMIN_EMAIL` y `SGI_INITIAL_ADMIN_PASSWORD`: bootstrap opcional de admin inicial
- `SGI_METRICS_ENABLED`: expone métricas Prometheus
- `SGI_SENTRY_DSN`: habilita captura de errores y tracing en Sentry
- `SGI_SENTRY_TRACES_SAMPLE_RATE`: porcentaje de traces enviados a Sentry

## Endpoints principales
- `GET /api/v1/health`
- `GET /api/v1/ready`
- `GET /metrics`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/change-password`
- `GET /api/v1/auth/me`
- `GET /api/v1/users`

## Migraciones
```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
alembic downgrade -1
```

## Calidad
```bash
ruff check .
black --check .
mypy app
pytest
pre-commit run --all-files
```

## Docker
```bash
docker compose up --build
```

La API queda expuesta en `http://localhost:8000` y PostgreSQL en `localhost:5432`.

## Observabilidad
- `GET /metrics` expone métricas Prometheus listas para scrapeo.
- Si configurás `SGI_SENTRY_DSN`, el starter reporta errores 5xx y transacciones a Sentry.
- Sentry tambien puede capturar spans de middleware y consultas de base de datos cuando configurás `SGI_SENTRY_TRACES_SAMPLE_RATE`.

## Notas de seguridad
- En `prod`, el starter obliga a usar un JWT secret fuerte y desactiva defaults inseguros.
- Los refresh tokens se guardan en base de datos, rotan en cada refresh y se revocan en logout y cambio de password.
- Si se reutiliza un refresh token ya rotado, se invalidan los tokens activos de ese usuario.
