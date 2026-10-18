# Arquitectura

Dashboard SQA usa Django con el patrón **MVT** (Modelo – Vista – Template). El navegador solo habla con las vistas de Django; nunca con la base de datos (R31).

## Responsabilidades por capa

| Capa | Hace | No hace |
|---|---|---|
| **Modelo** (`models.py`) | Define los datos y sus reglas. Toda consulta pasa por el ORM, que la parametriza (R23). | SQL armado a mano. |
| **Form** (`forms.py`) | Valida lo que manda el usuario y arma los mensajes de error por campo. | Guardar datos de otro usuario. |
| **Vista** (`views.py`) | Recibe la petición, filtra por `request.user`, usa el form y el modelo, y elige la plantilla o redirección. | Lógica de presentación. |
| **Template** (`templates/`) | Solo presenta lo que le da la vista. | Consultas o cálculos. |

## Estructura

```
dashboard-sqa/
├── config/            # settings, urls raíz, wsgi/asgi
├── apps/
│   ├── core/          # plantilla base, inicio, mixins compartidos
│   └── cuentas/       # crear cuenta, iniciar y cerrar sesión (R1)
├── templates/         # plantillas, una carpeta por app + base.html
├── static/            # css y js
└── docs/
```

## Apps previstas

Cada caso de uso vive en su propia app dentro de `apps/`:

| App | Caso de uso | Requisitos |
|---|---|---|
| `proyectos` | CU 01 · Iniciar el monitoreo de un proyecto | R2–R4 |
| `medidas` | CU 02 · Registrar las medidas del periodo | R5–R7 |
| `actividades` | CU 03 · Planear y dar seguimiento a las actividades SQA | R8–R9 |
| `tablero` | CU 04 · Evaluar la salud del proyecto | R10–R18 |
| `reportes` | CU 05 · Generar el reporte de salud | R19 |

Para crear una: `mkdir apps/<nombre> && python manage.py startapp <nombre> apps/<nombre>`, luego en su `apps.py` poner `name = "apps.<nombre>"` y agregarla a `INSTALLED_APPS`.

## Seguridad común

- **Sesión obligatoria (R20):** `LoginRequiredMiddleware` protege todas las pantallas. Solo las de acceso están marcadas con `@login_not_required`.
- **Cada quien sus datos (R21):** toda vista que lea o modifique datos de un usuario hereda de `apps.core.mixins.PropietarioMixin`. Un objeto ajeno responde 404.
- **Contraseñas (R22):** Django guarda solo el hash.
- **CSRF (R23):** todo `<form method="post">` lleva `{% csrf_token %}`.

## Convenciones de nombres

| Elemento | Convención | Ejemplo |
|---|---|---|
| Ruta (URL) | minúsculas con guiones | `proyectos/nuevo/` |
| Nombre de ruta | `app:snake_case` | `proyectos:nuevo` |
| Vista | `PascalCase` + `View` | `NuevoProyectoView` |
| Form | `PascalCase` + `Form` | `ProyectoPeriodoForm` |
| Plantilla | `templates/<app>/<snake_case>.html` | `templates/proyectos/mis_proyectos.html` |
| Pruebas | `apps/<app>/tests/test_<tema>.py` | `test_periodos.py` |

El código (nombres de variables, clases y mensajes) va en español, salvo lo que exige Django (`get_queryset`, `form_valid`, etc.).
