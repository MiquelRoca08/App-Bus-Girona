/**
 * Modal flotante con los horarios de una parada, abierto al tocar
 * cualquier parada en el minimapa (esté o no dentro del radio de
 * búsqueda actual del usuario).
 *
 * Los horarios se piden bajo demanda a /api/parada/{stop_id}/horarios,
 * reutilizando el mismo marcado (generarHTMLParada) que ya usa el
 * listado principal de paradas.
 */

import { generarHTMLParada, anadirEnlacePdfSiExiste } from "./render.js";

let idPeticionActual = 0;

function elementoModal() {
  return document.getElementById("modal-parada-mapa");
}

function elementoContenido() {
  return document.getElementById("modal-parada-mapa-contenido");
}

export function cerrarModalParadaMapa() {

  const modal = elementoModal();

  if (modal) {
    modal.classList.add("oculto");
  }

}

export async function abrirModalParadaMapa(stopId) {

  const modal = elementoModal();
  const contenido = elementoContenido();

  if (!modal || !contenido) {
    return;
  }

  // Invalida cualquier petición anterior todavía en vuelo: si el
  // usuario toca varias paradas seguidas rápido, solo debe pintarse
  // la respuesta de la última que tocó.
  const miPeticionId = ++idPeticionActual;

  contenido.innerHTML = `
    <p class="status-text">Cargando horarios…</p>
  `;

  modal.classList.remove("oculto");

  try {

    const respuesta = await fetch(
      `/api/parada/${encodeURIComponent(stopId)}/horarios`
    );

    if (miPeticionId !== idPeticionActual) {
      // Llegó tarde: el usuario ya tocó otra parada, ignorar.
      return;
    }

    if (!respuesta.ok) {

      contenido.innerHTML = `
        <p class="status-text">
          No se han podido cargar los horarios de esta parada.
        </p>
      `;

      return;

    }

    const datos = await respuesta.json();

    // generarHTMLParada espera la misma forma que las entradas de
    // data.paradas del listado principal: { parada, proximos_autobuses,
    // fuente_horarios, tiempo_real_disponible }. El endpoint por
    // stop_id ya devuelve exactamente esa forma.
    contenido.innerHTML = generarHTMLParada(datos);

    anadirEnlacePdfSiExiste(datos.parada.stop_id);

  } catch (error) {

    if (miPeticionId !== idPeticionActual) {
      return;
    }

    console.warn(
      `No se pudieron cargar los horarios de la parada ${stopId}:`,
      error
    );

    contenido.innerHTML = `
      <p class="status-text">
        No se han podido cargar los horarios de esta parada.
      </p>
    `;

  }

}
