/**
 * Punto de entrada. Expone en `window` las funciones que el HTML
 * invoca directamente mediante onclick, y arranca la búsqueda al
 * cargar la página.
 */

import { recentrarUbicacion } from "./mapa.js";
import { buscarAutobuses } from "./ubicacion.js";
import {
  abrirPanelConfig,
  cerrarPanelConfig,
  guardarPanelConfig,
} from "./panel-config.js";
import { abrirAbout, cerrarAbout, actualizarVersion } from "./about.js";

// Nota: el chequeo de versión y el auto-reset ante una versión nueva del
// servidor viven ahora en un <script> al principio de <head> en index.html
// (se ejecuta antes de cargar este módulo), combinado con cabeceras
// Cache-Control en el servidor. Ya no hace falta cache-bustear el CSS aquí
// a mano.

window.recentrarUbicacion = recentrarUbicacion;
window.buscarAutobuses = buscarAutobuses;
window.abrirPanelConfig = abrirPanelConfig;
window.cerrarPanelConfig = cerrarPanelConfig;
window.abrirAbout = abrirAbout;
window.cerrarAbout = cerrarAbout;

window.guardarPanelConfig = () => {
  guardarPanelConfig();
  buscarAutobuses();
};

window.addEventListener("load", () => {
  // Mostrar versión en el footer y lanzar la búsqueda
  actualizarVersion();
  buscarAutobuses();
});
