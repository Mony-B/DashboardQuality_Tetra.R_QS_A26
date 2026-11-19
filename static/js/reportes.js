/* CU 05 · Reportes: al cambiar de proyecto se recarga el formulario con su periodo actual.
   El periodo y las secciones se eligen sin recargar; no se guarda nada (FE-1). */
(function () {
  "use strict";

  var formulario = document.getElementById("form-reportes");
  if (!formulario) return;
  var selProyecto = document.getElementById("selector-proyecto");
  var selPeriodo = document.getElementById("selector-periodo");

  selProyecto.addEventListener("change", function () {
    // Sin periodo en la dirección, el servidor abre el periodo actual del proyecto elegido.
    selPeriodo.disabled = true;
    formulario.submit();
  });
})();
