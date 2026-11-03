// FE-1: si el usuario ya capturó algún dato, pide confirmación antes de descartarlo.
// Sin JavaScript, "Cancelar" simplemente regresa a Mis proyectos sin guardar.
(function () {
  const form = document.getElementById("form-proyecto");
  const cancelar = document.getElementById("cancelar");
  const dialogo = document.getElementById("confirmar-cancelar");
  if (!form || !cancelar || !dialogo || typeof dialogo.showModal !== "function") return;

  const editables = () =>
    Array.from(form.querySelectorAll("input:not([type=hidden]):not([disabled]), textarea:not([disabled])"));

  // Valores al cargar: si el formulario regresó con errores, ya trae datos capturados.
  const iniciales = new Map(editables().map((el) => [el, el.defaultValue]));
  const hayDatos = () => editables().some((el) => el.value.trim() !== "" || el.value !== iniciales.get(el));

  cancelar.addEventListener("click", (evento) => {
    if (!hayDatos()) return;
    evento.preventDefault();
    dialogo.showModal();
  });

  dialogo.querySelector("[data-accion=seguir]").addEventListener("click", () => dialogo.close());
})();
