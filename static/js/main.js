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

// Intento de cache-bust para CSS en despliegues donde el fichero está cacheado
(async function bustCssCache() {
  try {
    const resp = await fetch("/api/about", { cache: "no-store" });
    if (!resp.ok) return;
    const data = await resp.json();
    const v = encodeURIComponent(data.version || Date.now());
    const links = document.querySelectorAll('link[rel="stylesheet"]');
    // fallback selector if above returns none
    const cssLinks = links.length ? links : document.querySelectorAll('link[rel="stylesheet"][href*="styles.css"]');
    cssLinks.forEach((l) => {
      try {
        const href = l.getAttribute("href") || l.href;
        const url = new URL(href, location.href);
        url.searchParams.set("v", v);
        l.setAttribute("href", url.toString());
      } catch (err) {
        // ignore
      }
    });
  } catch (err) {
    console.debug("No se pudo cache-bustear CSS:", err);
  }
})();

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
