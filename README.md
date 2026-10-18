# DashboardQuality · Tetra.R (QS A26)

**Dashboard SQA**

Centro de control de la calidad para equipos de desarrollo: registra proyectos por periodo, captura sus medidas de calidad, calcula 5 métricas basadas en la ISO/IEC 25010 y genera reportes de salud.

**Equipo Tetra.R** · Django 5.2 · patrón MVT

## Arrancar en tu máquina

Requiere Python 3.12 o superior.

```bash
# 1. Entorno virtual
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Dependencias (incluye ruff, bandit y coverage)
pip install -r requirements-dev.txt

# 3. Variables de entorno
cp .env.example .env               # Windows: copy .env.example .env

# 4. Base de datos y usuario administrador
#    (solo quien sube el repo por primera vez: python manage.py makemigrations cuentas,
#     y hace commit de apps/cuentas/migrations/0001_initial.py)
python manage.py migrate
python manage.py createsuperuser

# 5. Correr
python manage.py runserver
```

Abre http://127.0.0.1:8000/ y crea una cuenta.

## Calidad

```bash
ruff check .                                   # estilo y errores
bandit -c pyproject.toml -r apps config -lll   # seguridad
coverage run manage.py test && coverage report # pruebas y cobertura
```

El CI de GitHub corre lo mismo en cada pull request. El flujo completo está en [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentación

- [Arquitectura y convenciones](docs/arquitectura.md)
- Requisitos, casos de uso, estrategia de calidad y evidencia: carpeta compartida del equipo en Drive.
