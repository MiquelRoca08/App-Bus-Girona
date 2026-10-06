/**
 * Indicador de texto "Última actualización: hace Xs", mostrado debajo
 * del botón de actualizar. Se refresca cada segundo para dar feedback
 * en vivo, independientemente de si la actualización de horarios fue
 * manual (botón) o automática (auto-refresh.js).
 */

let momentoUltimaActualizacion = null;
let intervaloTexto = null;

function formatearHaceTiempo(segundos) {

  if (segundos < 5) {
    return "justo ahora";
  }

  if (segundos < 60) {
    return `hace ${segundos}s`;
  }

  const minutos = Math.floor(segundos / 60);

  if (minutos === 1) {
    return "hace 1 min";
  }

  return `hace ${minutos} min`;

}

function pintarTexto() {

  const elemento = document.getElementById("ultima-actualizacion");

  if (!elemento || momentoUltimaActualizacion === null) {
    return;
  }

  const segundos = Math.floor(
    (Date.now() - momentoUltimaActualizacion) / 1000
  );

  elemento.textContent =
    `Última actualización: ${formatearHaceTiempo(segundos)}`;

}

/**
 * Marca "ahora" como el momento de la última actualización y arranca
 * (si no estaba ya en marcha) el refresco del texto cada segundo.
 * Se llama tras cada actualización de horarios, manual o automática.
 */
export function registrarActualizacion() {

  momentoUltimaActualizacion = Date.now();

  pintarTexto();

  if (intervaloTexto === null) {
    intervaloTexto = setInterval(pintarTexto, 1000);
  }

}
