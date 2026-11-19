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

## Apps por caso de uso

Cada caso de uso vive en su propia app dentro de `apps/`:

| App | Caso de uso | Requisitos | Estado |
|---|---|---|---|
| `proyectos` | CU 01 · Iniciar el monitoreo de un proyecto | R2–R4 | Implementado |
| `medidas` | CU 02 · Registrar las medidas del periodo | R5–R7 | Implementado (guarda las medidas en `Periodo`) |
| `actividades` | CU 03 · Planear y dar seguimiento a las actividades SQA | R8–R9 | Implementado |
| `tablero` | CU 04 · Evaluar la salud del proyecto en un periodo | R10–R18 | Implementado |
| `reportes` | CU 05 · Generar el reporte de salud de un periodo | R19 | Implementado |

## Modelo de datos (hasta CU 01)

- **Proyecto**: `usuario`, `nombre` (≤ 100, único por usuario), `marco_trabajo` (≤ 50), `descripcion` (≤ 500, opcional).
- **Periodo**: `proyecto`, `nombre` (≤ 50, único por proyecto), `fecha_inicio`, `fecha_fin` (≥ inicio, la BD lo valida). Los periodos de un proyecto no se traslapan (lo valida el form). El periodo actual es el de inicio más reciente.
- Las medidas del periodo (CU 02) viven en `Periodo`: ocho campos, vacíos hasta que se capturan.

## Reporte de salud (CU 05)

Una sola pantalla en `/reportes/`: sin `generar` en la URL muestra el formulario; con `generar` valida (proyecto y periodo del usuario, al menos una sección, periodo con medidas) y muestra el reporte en el navegador. No se guarda ni se exporta: se imprime con el navegador (`@media print` en `reportes.css`). Reutiliza el cálculo de `apps/tablero` para que sus valores coincidan con el Dashboard, y `apps/core/seleccion.py` para elegir proyecto y periodo de forma segura.

## Salud del periodo (CU 04)

No se guarda: se calcula en el momento con las ocho medidas, así el Dashboard y Mis proyectos siempre reflejan lo último guardado.

- `apps/tablero/calculo.py`: Python puro (sin ORM). Fórmulas de las cuatro métricas, semáforos, puntos (100/60/0), pesos (25/30/20/25), índice, estado y las reglas R16 (sin datos → «Sin evaluar») y R18. Es la única fuente de umbrales y pesos.
- `apps/tablero/grafica.py`: coordenadas de la gráfica de tendencia; la plantilla dibuja el SVG en el servidor, sin JavaScript de gráficas.
- `apps/tablero/presentacion.py`: textos del Dashboard (motivo, medida faltante, tabla de reglas).
- `Periodo.salud()` y `Periodo.recalcular_salud()` envuelven el cálculo; `Proyecto.resumen_salud()` alimenta la tarjeta de Mis proyectos.

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
