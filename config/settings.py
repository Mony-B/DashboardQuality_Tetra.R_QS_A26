"""Configuración de Django para Dashboard SQA.

Los valores sensibles o que cambian por entorno se leen de variables de entorno
(archivo .env en desarrollo; ver .env.example).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _env_bool(nombre: str, por_defecto: bool = False) -> bool:
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes"}


def _env_lista(nombre: str, por_defecto: str = "") -> list[str]:
    return [v.strip() for v in os.environ.get(nombre, por_defecto).split(",") if v.strip()]


# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
DEBUG = _env_bool("DJANGO_DEBUG", por_defecto=False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "solo-desarrollo-no-usar-en-produccion"  # nosec B105
    else:
        raise ImproperlyConfigured("Define DJANGO_SECRET_KEY (ver .env.example).")

ALLOWED_HOSTS = _env_lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

if not DEBUG:
    SESSION_COOKIE_SECURE = _env_bool("DJANGO_COOKIES_SEGURAS", por_defecto=True)
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps del proyecto (una por dominio / caso de uso; ver docs/arquitectura.md)
    "apps.core",
    "apps.cuentas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # R20: todas las pantallas piden sesión, salvo las marcadas con @login_not_required
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Base de datos (solo se accede por el ORM; R23)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Autenticación (R1, R22: Django guarda solo el hash de la contraseña)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "cuentas.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "cuentas:iniciar_sesion"
LOGIN_REDIRECT_URL = "core:inicio"
LOGOUT_REDIRECT_URL = "cuentas:iniciar_sesion"

# ---------------------------------------------------------------------------
# Idioma y zona horaria (R27: interfaz en español)
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Archivos estáticos (el sistema no almacena archivos de usuarios; R32)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
