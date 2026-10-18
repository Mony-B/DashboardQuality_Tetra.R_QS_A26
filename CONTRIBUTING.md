# Cómo contribuir

Seguimos el flujo de la Estrategia de Aseguramiento de Calidad: **ningún cambio se integra sin checklist, revisión y pruebas.**

## Flujo de un cambio

1. **Requisito / CU:** la especificación del CU tiene su checklist de requisitos aprobada.
2. **Diseño:** el diagrama y el modelo de datos pasan la checklist de diseño.
3. **Código:** trabajas en tu rama y haces tu revisión personal con la checklist de código.
4. **Revisión entre pares (compuerta principal):** abres un pull request. Otra persona lo revisa con la checklist. El CI debe pasar.
5. **Integración:** se hace merge a `main`.
6. **Pruebas de integración:** se prueba que lo nuevo no rompe lo de los demás.
7. **Entrega:** punto de control.

Todo defecto que aparezca en cualquier paso se corrige antes de seguir.

## Ramas

- `main` está protegida: solo entra por pull request aprobado.
- Una rama por caso de uso o tarea: `cu01-iniciar-monitoreo`, `cu02-captura-medidas`, `fix-validacion-fechas`.

## Antes de abrir el pull request

```bash
ruff check .
ruff format .
bandit -c pyproject.toml -r apps config -lll
coverage run manage.py test
coverage report
```

Para guardar la evidencia en Drive:

```bash
mkdir -p reportes
ruff check . --output-file reportes/ruff.txt
bandit -c pyproject.toml -r apps config -f txt -o reportes/bandit.txt
coverage html -d reportes/cobertura
```

## Revisión entre pares

A revisa a B y B revisa a A. El revisor usa la plantilla del pull request y la checklist de código del equipo, y deja el enlace a la checklist llenada en Drive.
