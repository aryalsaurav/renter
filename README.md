# Renter 🏠

A Django rental-listing platform where **anyone can browse available houses and
apartments without logging in** — they see photos and location details, but the
**owner's contact info stays hidden**. To publish a listing you must create an
account and log in; submissions are validated and moderated.

Everything is exposed **twice**:

- a **JSON API** (DRF) secured with **JWT** authentication, and
- server-rendered **Django templates** secured with **session/cookie** auth.

## Stack

| Concern            | Tech                                             |
| ------------------ | ------------------------------------------------ |
| Web framework      | Django 5                                         |
| API                | Django REST Framework + SimpleJWT + drf-spectacular |
| Database           | PostgreSQL                                        |
| Cache / broker     | Redis                                             |
| Async tasks        | Celery + Celery Beat (`django-celery-beat`)       |
| Media (local)      | Local filesystem                                  |
| Media (prod)       | AWS S3 (`django-storages` + `boto3`)              |
| Static (prod)      | WhiteNoise                                         |
| Packaging          | Poetry                                            |
| Tests              | pytest + pytest-django + factory-boy              |
| Containers         | Docker + Docker Compose (separate local & prod)   |

## Project layout

```
renter/
├── config/                     # Django project (settings, urls, celery, wsgi)
│   ├── settings/{base,local,prod,test}.py
│   ├── urls.py                 # template routes + /api/ + /api/docs/
│   ├── api_urls.py             # API root (JWT endpoints + app routers)
│   └── celery.py
├── apps/
│   ├── accounts/               # custom email user, profiles, auth
│   │   ├── api/{serializers,views,urls}.py   # JWT API
│   │   ├── views.py urls.py forms.py         # session/template
│   │   └── tests/
│   └── listings/               # the core rental domain
│       ├── api/{serializers,views,urls,permissions,filters}.py
│       ├── views.py urls.py forms.py tasks.py admin.py
│       └── tests/
├── templates/                  # Bootstrap-based UI
├── docker/{local,prod}/django/ # Dockerfiles + start scripts
├── docker-compose.local.yml
├── docker-compose.prod.yml
├── scripts/                    # run / migrate helpers
├── .env / .env.example         # local env
└── .env.prod.sample.txt        # production env sample
```

Imports use absolute paths (e.g. `from apps.listings.api.serializers import ...`).

## How visibility & permissions work

- **Anonymous visitor** — can browse/search published+available listings and open
  a detail page (photos + location). `owner_contact` is `null` in the API and the
  template shows a "Log in to view" lock.
- **Authenticated user** — everything above **plus** owner contact details, and
  can create listings.
- **Owner** — can edit/delete only their own listings (`IsOwnerOrReadOnly`).
- **Moderation/validation** — new listings from *unverified* users go to a
  `pending` queue (a Celery task emails moderators); *verified* owners publish
  instantly. Admins approve/reject from the dashboard.

| Surface  | Auth            | Login                          |
| -------- | --------------- | ------------------------------ |
| Templates| Session + CSRF  | `/accounts/login/`             |
| API      | JWT (Bearer)    | `POST /api/auth/token/`        |

## Quick start — Local (Docker)

Requires Docker + Docker Compose.

```bash
# 1. Create your local env file (defaults work out of the box)
cp .env.example .env

# 2. Build and start everything (web + worker + beat + postgres + redis)
./scripts/local.sh
```

Then open:

- App (templates): http://localhost:8000/
- Admin dashboard: http://localhost:8000/admin/  (default `admin@renter.local` / `admin12345`)
- API docs (Swagger): http://localhost:8000/api/docs/

The local web container automatically runs `makemigrations`, `migrate`,
`collectstatic`, and creates the superuser from `DJANGO_SUPERUSER_*`.
Media files are written to the local `media/` volume.

## Quick start — Production (Docker)

Production stores media on **AWS S3** and serves static files with WhiteNoise
behind an Nginx reverse proxy.

```bash
# 1. Create the production env file from the sample and fill in real secrets
cp .env.prod.sample.txt .env.prod
$EDITOR .env.prod          # set SECRET_KEY, DB creds, AWS keys, SMTP, hosts...

# 2. Build images and start the stack (NO migrations are run here)
./scripts/prod.sh

# 3. Run migrations as a separate, deliberate release step
./scripts/migrate_prod.sh

# 4. Create an admin user
./scripts/createsuperuser_prod.sh
```

> The production web `start.sh` intentionally **does not run migrations** —
> only `collectstatic` + Gunicorn. Apply schema changes explicitly with
> `scripts/migrate_prod.sh` during a controlled release.

App is served by Nginx on port 80 → Gunicorn.

## API reference

Auth:

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"strongpass123!","password2":"strongpass123!"}'

# Obtain JWT
curl -X POST http://localhost:8000/api/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"strongpass123!"}'
```

Key endpoints:

| Method | Path                                | Auth        | Purpose                          |
| ------ | ----------------------------------- | ----------- | -------------------------------- |
| GET    | `/api/listings/`                    | public      | browse/search published listings |
| GET    | `/api/listings/{slug}/`             | public      | detail (owner contact hidden)    |
| POST   | `/api/listings/`                    | JWT         | create a listing                 |
| PATCH  | `/api/listings/{slug}/`             | JWT (owner) | update own listing               |
| DELETE | `/api/listings/{slug}/`             | JWT (owner) | delete own listing               |
| GET    | `/api/listings/mine/`               | JWT         | the caller's own listings        |
| POST   | `/api/listings/{slug}/images/`      | JWT (owner) | upload an image                  |
| GET/PATCH | `/api/auth/me/`                  | JWT         | self profile                     |

Filters/search: `?city=`, `?property_type=`, `?min_rent=`, `?max_rent=`,
`?min_bedrooms=`, `?search=`, `?ordering=monthly_rent`.

## Background tasks (Celery + Beat)

- `notify_new_listing` — emails moderators when an unverified owner submits.
- `notify_listing_status_change` — emails the owner on approve/reject.
- `deactivate_stale_pending_listings` — **beat**, daily 03:00: auto-rejects
  listings stuck pending > 30 days.
- `daily_listing_digest` — **beat**, daily 08:00: logs published count.

## Running tests

```bash
poetry install --with dev
poetry run pytest
```

Tests run against fast in-memory SQLite (`config.settings.test`) with Celery in
eager mode — no Postgres/Redis needed. 33 tests cover models, tasks, the JWT API
(including the public/owner visibility rules), and the session-auth templates.

## Local development without Docker

```bash
poetry install --with dev
# Make sure Postgres + Redis are running and .env points at them, then:
poetry run python manage.py migrate
poetry run python manage.py runserver
```
