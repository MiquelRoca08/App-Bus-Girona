/**
 * Punto de entrada. Enlaza los botones del HTML con sus funciones
 * y arranca la búsqueda al cargar la página.
 */

import { recentrarUbicacion } from "./mapa.js";
import { buscarAutobuses } from "./ubicacion.js";
import {
  abrirPanelConfig,
  cerrarPanelConfig,
  guardarPanelConfig,
} from "./panel-config.js";
import { abrirAbout, cerrarAbout, actualizarVersion } from "./about.js";
import { iniciarAutoActualizacion } from "./auto-refresh.js";
import { cerrarModalParadaMapa } from "./modal-parada-mapa.js";

// Nota: el chequeo de versión y el auto-reset ante una versión nueva del
// servidor viven ahora en un <script> al principio de <head> en index.html
// (se ejecuta antes de cargar este módulo), combinado con cabeceras
// Cache-Control en el servidor. Ya no hace falta cache-bustear el CSS aquí
// a mano.

const alPulsar = (id, fn) =>
  document.getElementById(id).addEventListener("click", fn);

alPulsar("btn-recentrar", recentrarUbicacion);
alPulsar("btn-actualizar", buscarAutobuses);
alPulsar("btn-abrir-config", abrirPanelConfig);
alPulsar("btn-cancelar-config", cerrarPanelConfig);
alPulsar("btn-abrir-about", abrirAbout);
alPulsar("btn-cerrar-about", cerrarAbout);
alPulsar("btn-cerrar-parada", cerrarModalParadaMapa);
alPulsar("btn-guardar-config", () => {
  guardarPanelConfig();
  buscarAutobuses();
});

window.addEventListener("load", () => {
  // Mostrar versión en el footer y lanzar la búsqueda
  actualizarVersion();
  buscarAutobuses();

  // A partir de aquí, refrescar automáticamente cada minuto en punto
  // (segundo :00 del reloj del dispositivo), igual que la web de TMG.
  iniciarAutoActualizacion(buscarAutobuses);
});
