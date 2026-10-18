## Qué cambia

<!-- Caso de uso y requisitos que cubre, p. ej. "CU 01 · R2, R3, R4" -->

## Revisión personal (autor)

- [ ] Llené la checklist de código y la guardé en Drive: <!-- enlace -->
- [ ] `ruff check .` y `ruff format --check .` sin errores
- [ ] `bandit -c pyproject.toml -r apps config -lll` sin hallazgos altos
- [ ] `python manage.py test` pasa y agregué pruebas para lo nuevo
- [ ] Si cambié modelos, incluí las migraciones

## Revisión entre pares (revisor)

- [ ] Archivos en la app o carpeta que les corresponde
- [ ] Respeta MVT: el Modelo accede a la BD, la Vista filtra por el usuario, el Template solo presenta
- [ ] Toda vista con datos de usuario usa `PropietarioMixin` (o filtra por `request.user`)
- [ ] Rutas, vistas y plantillas siguen la convención de nombres
- [ ] La pantalla coincide con el wireframe y muestra los mensajes de error junto al campo
- [ ] Cumple precondiciones, flujo normal, flujos alternativos y de excepción del CU
- [ ] Checklist de revisión entre pares guardada en Drive: <!-- enlace -->
