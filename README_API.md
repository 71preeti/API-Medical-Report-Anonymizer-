Iamstillalive - API scaffold
============================

This scaffold adds a simple `api` Django app exposing a `Report` resource
and JWT authentication endpoints (via djangorestframework-simplejwt).

Key files added:
- api/models.py
- api/serializers.py
- api/views.py
- api/urls.py
- requirements.txt (updated)
- .gitignore

Important commands
------------------
# create venv and install deps
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# run migrations & create superuser
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# run server
python manage.py runserver

Endpoints
---------
POST /api/v1/auth/token/        -> get access & refresh tokens (body: username, password)
POST /api/v1/auth/token/refresh/-> refresh access token (body: refresh)
GET/POST /api/v1/reports/       -> list or create reports (requires Authorization: Bearer <token>)
GET/PUT/DELETE /api/v1/reports/<id>/ -> retrieve/update/delete a report

CORS
----
Configure CORS_ALLOWED_ORIGINS in environment variable CORS_ALLOWED_ORIGINS as comma-separated list.

Security note
-------------
- SECRET_KEY is now read from env var DJANGO_SECRET_KEY (default safe-only-for-dev placeholder).
- Remove any committed secrets before sharing or deploying.
