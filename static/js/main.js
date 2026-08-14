/**
 * Punto de entrada. Expone en `window` las funciones que el HTML
 * invoca directamente mediante onclick, y arranca la búsqueda al
 * cargar la página.
 */

import { recentrarUbicacion } from "./mapa.js";
import { buscarAutobuses } from "./ubicacion.js";

window.recentrarUbicacion = recentrarUbicacion;
window.buscarAutobuses = buscarAutobuses;

window.addEventListener(
  "load",
  buscarAutobuses
);
