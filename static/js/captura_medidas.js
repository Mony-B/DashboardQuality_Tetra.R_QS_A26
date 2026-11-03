/* CU 02 · Captura de medidas: selectores de proyecto y periodo, y confirmaciones (FA-4, FE-1). */
(function () {
  "use strict";

  var formulario = document.getElementById("form-medidas");
  var selProyecto = document.getElementById("selector-proyecto");
  var selPeriodo = document.getElementById("selector-periodo");
  var datos = JSON.parse(document.getElementById("datos-selector").textContent);

  // ¿Hay cambios sin guardar? Se compara contra los valores con que se cargó la pantalla.
  var inicial = valoresActuales();

  function valoresActuales() {
    return Array.prototype.map
      .call(formulario.elements, function (el) {
        if (!el.name || el.name === "csrfmiddlewaretoken") return "";
        return el.type === "checkbox" ? String(el.checked) : el.value;
      })
      .join("|");
  }

  function hayCambios() {
    return valoresActuales() !== inicial;
  }

  function llenarProyectos() {
    datos.forEach(function (p) {
      var o = new Option(p.nombre, p.id, false, String(p.id) === selProyecto.dataset.actual);
      selProyecto.add(o);
    });
  }

  function llenarPeriodos(proyectoId, periodoId) {
    selPeriodo.innerHTML = "";
    var proyecto = datos.find(function (p) { return String(p.id) === String(proyectoId); });
    (proyecto ? proyecto.periodos : []).forEach(function (p) {
      selPeriodo.add(new Option(p.etiqueta, p.id, false, String(p.id) === String(periodoId)));
    });
  }

  // Diálogo de confirmación: devuelve true en «confirmar» y false en «seguir editando».
  function confirmar(dialogo, alConfirmar, alRechazar) {
    dialogo.querySelector("[data-confirmar]").onclick = function () {
      dialogo.close();
      alConfirmar();
    };
    dialogo.querySelector("[data-cerrar]").onclick = function () {
      dialogo.close();
      if (alRechazar) alRechazar();
    };
    dialogo.oncancel = function () { if (alRechazar) alRechazar(); };
    dialogo.showModal();
  }

  function ir(url) {
    window.location.href = url;
  }

  function restaurarSelectores() {
    selProyecto.value = selProyecto.dataset.actual;
    llenarPeriodos(selProyecto.dataset.actual, selPeriodo.dataset.actual);
  }

  function cambiarA(url) {
    if (!url) return;
    if (!hayCambios()) return ir(url);
    confirmar(document.getElementById("dialogo-cambiar"), function () { ir(url); }, restaurarSelectores);
  }

  llenarProyectos();
  llenarPeriodos(selProyecto.dataset.actual, selPeriodo.dataset.actual);

  selPeriodo.addEventListener("change", function () {
    var proyecto = datos.find(function (p) { return String(p.id) === selProyecto.value; });
    var periodo = proyecto && proyecto.periodos.find(function (p) { return String(p.id) === selPeriodo.value; });
    cambiarA(periodo && periodo.url);
  });

  // Al cambiar de proyecto se abre su periodo actual (el de fecha de inicio más reciente, que va primero).
  selProyecto.addEventListener("change", function () {
    var proyecto = datos.find(function (p) { return String(p.id) === selProyecto.value; });
    if (!proyecto || proyecto.periodos.length === 0) return restaurarSelectores();
    cambiarA(proyecto.periodos[0].url);
  });

  document.getElementById("boton-cancelar").addEventListener("click", function (evento) {
    var destino = evento.currentTarget.dataset.destino;
    if (!hayCambios()) return ir(destino);
    confirmar(document.getElementById("dialogo-cancelar"), function () { ir(destino); });
  });
})();
