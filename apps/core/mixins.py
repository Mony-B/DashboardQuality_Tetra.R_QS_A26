"""Mixins compartidos por las vistas de todas las apps."""


class PropietarioMixin:
    """Limita el queryset de la vista a los objetos del usuario autenticado (R21).

    Úsalo en toda vista basada en clase que lea o modifique datos de un usuario.
    Si el objeto pertenece a otra persona, get_object() no lo encuentra y la
    vista responde 404, sin revelar que existe.

        class DetalleProyectoView(PropietarioMixin, DetailView):
            model = Proyecto

    Si el dueño no está en un campo llamado ``usuario`` (por ejemplo, un periodo
    cuyo dueño es el del proyecto), indica la ruta en ``campo_propietario``:

        campo_propietario = "proyecto__usuario"
    """

    campo_propietario = "usuario"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(**{self.campo_propietario: self.request.user})
