/**
 * Utilidades generales.
 */

export function escaparHTML(texto) {

  if (texto === null || texto === undefined) {
    return "";
  }

  const div = document.createElement("div");

  div.textContent = String(texto);

  return div.innerHTML;
}
