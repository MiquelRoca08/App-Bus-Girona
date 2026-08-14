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

window.recentrarUbicacion = recentrarUbicacion;
window.buscarAutobuses = buscarAutobuses;
window.abrirPanelConfig = abrirPanelConfig;
window.cerrarPanelConfig = cerrarPanelConfig;

window.guardarPanelConfig = () => {
  guardarPanelConfig();
  buscarAutobuses();
};

window.addEventListener(
  "load",
  buscarAutobuses
);
