/* CU 04 · Dashboard: cambiar de proyecto, periodo o métrica recarga la pantalla (FA-3).
   No hay confirmación porque aquí no se captura nada. */
(function () {
  "use strict";

  var formulario = document.getElementById("form-dashboard");
  var selProyecto = document.getElementById("selector-proyecto");
  var selPeriodo = document.getElementById("selector-periodo");
  var selMetrica = document.getElementById("selector-metrica");
  var ocultoMetrica = formulario && formulario.querySelector('input[name="metrica"]');

  if (!formulario) return;

  // Al cambiar de proyecto no se manda el periodo: abre su periodo actual.
  selProyecto.addEventListener("change", function () {
    selPeriodo.disabled = true;
    formulario.submit();
  });

  selPeriodo.addEventListener("change", function () {
    formulario.submit();
  });

  // La tendencia conserva proyecto y periodo y solo cambia la métrica.
  selMetrica.addEventListener("change", function () {
    document.getElementById("form-metrica").submit();
  });

  if (ocultoMetrica && selMetrica) ocultoMetrica.value = selMetrica.value;
})();
