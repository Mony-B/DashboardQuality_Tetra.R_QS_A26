/* CU 03 · Actividades SQA: selectores de proyecto y periodo, cambio de estado inmediato
   el aviso de que una actividad planeada no se edita y la confirmación al cancelar (FE-1). Sin JavaScript, el estado se guarda
   con el botón "Guardar" de cada fila y "Cancelar" vuelve a cargar la pantalla. */
(function () {
  "use strict";

  var datos = JSON.parse(document.getElementById("datos-selector").textContent);
  var selProyecto = document.getElementById("selector-proyecto");
  var selPeriodo = document.getElementById("selector-periodo");

  function buscarProyecto(id) {
    return datos.find(function (p) { return String(p.id) === String(id); });
  }

  function llenarPeriodos(proyectoId, periodoId) {
    selPeriodo.innerHTML = "";
    var proyecto = buscarProyecto(proyectoId);
    (proyecto ? proyecto.periodos : []).forEach(function (p) {
      selPeriodo.add(new Option(p.etiqueta, p.id, false, String(p.id) === String(periodoId)));
    });
  }

  datos.forEach(function (p) {
    selProyecto.add(new Option(p.nombre, p.id, false, String(p.id) === selProyecto.dataset.actual));
  });
  llenarPeriodos(selProyecto.dataset.actual, selPeriodo.dataset.actual);

  selPeriodo.addEventListener("change", function () {
    var proyecto = buscarProyecto(selProyecto.value);
    var periodo = proyecto && proyecto.periodos.find(function (p) { return String(p.id) === selPeriodo.value; });
    if (periodo) window.location.href = periodo.url;
  });

  // Al cambiar de proyecto se abre su periodo actual (el de inicio más reciente, que va primero).
  selProyecto.addEventListener("change", function () {
    var proyecto = buscarProyecto(selProyecto.value);
    if (proyecto && proyecto.periodos.length) window.location.href = proyecto.periodos[0].url;
    else llenarPeriodos(selProyecto.dataset.actual, selPeriodo.dataset.actual);
  });

  // Pasos 8 y 9: al elegir otro estado se guarda de inmediato.
  document.querySelectorAll(".form-estado select").forEach(function (sel) {
    sel.addEventListener("change", function () { sel.form.submit(); });
  });

  // Aviso: una actividad planeada ya no se puede editar. Se pide confirmar antes de registrarla.
  var formPlanear = document.getElementById("form-actividad");
  var avisoPlanear = document.getElementById("confirmar-planear");
  if (formPlanear && avisoPlanear && typeof avisoPlanear.showModal === "function") {
    var confirmado = false;
    formPlanear.addEventListener("submit", function (evento) {
      if (confirmado) return;
      evento.preventDefault();
      avisoPlanear.showModal();
    });
    avisoPlanear.querySelector("[data-accion=revisar]").addEventListener("click", function () {
      avisoPlanear.close();
    });
    avisoPlanear.querySelector("[data-accion=planear]").addEventListener("click", function () {
      confirmado = true;
      avisoPlanear.close();
      formPlanear.submit();
    });
  }

  // FE-1: si ya eligió o capturó algún dato, pide confirmación antes de vaciar el formulario.
  var form = document.getElementById("form-actividad");
  var cancelar = document.getElementById("cancelar");
  var dialogo = document.getElementById("confirmar-cancelar");
  if (!form || !cancelar || !dialogo || typeof dialogo.showModal !== "function") return;

  var campos = Array.prototype.slice.call(
    form.querySelectorAll("select, input:not([type=hidden])")
  );

  function hayDatos() {
    return campos.some(function (el) { return el.value.trim() !== ""; });
  }

  function vaciar() {
    campos.forEach(function (el) { el.value = ""; });
    form.querySelectorAll(".error").forEach(function (el) { el.remove(); });
    form.querySelectorAll(".campo-error").forEach(function (el) { el.classList.remove("campo-error"); });
  }

  cancelar.addEventListener("click", function (evento) {
    evento.preventDefault();
    if (hayDatos()) dialogo.showModal();
    else vaciar();
  });
  dialogo.querySelector("[data-accion=seguir]").addEventListener("click", function () { dialogo.close(); });
  dialogo.querySelector("[data-accion=confirmar]").addEventListener("click", function () {
    dialogo.close();
    vaciar();
  });
})();
