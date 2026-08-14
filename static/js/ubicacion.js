/**
 * Obtención de ubicación GPS y consulta al backend para buscar la
 * parada más cercana y sus próximos autobuses.
 */

import { escaparHTML } from "./utils.js";
import { inicializarOActualizarMapa } from "./mapa.js";
import { mostrarResultados } from "./render.js";
import { obtenerConfig } from "./config.js";

const API_URL = "/api/proxima-parada";


export function buscarAutobuses() {

  const contenedor =
    document.getElementById(
      "contenido"
    );


  const boton =
    document.getElementById(
      "btn-actualizar"
    );


  /* Estado inicial */

  contenedor.innerHTML = `

    <p class="status-text">

      Obteniendo tu ubicación GPS...

    </p>

  `;


  boton.disabled = true;


  /* ========================================================
     Comprobar GPS
     ======================================================== */

  if (!navigator.geolocation) {

    contenedor.innerHTML = `

      <p class="status-text error-text">

        El GPS no está disponible
        en este dispositivo.

      </p>

    `;

    boton.disabled = false;

    return;

  }


  /* ========================================================
     Comprobar permisos (Permissions API)
     Si están denegados, mostrar un modal con instrucciones
     ======================================================== */

  if (navigator.permissions && navigator.permissions.query) {

    try {

      navigator.permissions
        .query({ name: "geolocation" })
        .then((perm) => {

          if (perm.state === "denied") {

            mostrarModalActivarUbicacion();

            boton.disabled = false;

            return;

          }

          // Si está 'prompt' o 'granted', continuar y solicitar posición
          solicitarPosicion();

        })
        .catch((e) => {

          // Si falla la query de permisos, intentar obtener la posición
          console.warn("Permissions API falla:", e);

          solicitarPosicion();

        });

      // Salimos de la función aquí; la continuación ocurre en solicitarPosicion()
      return;

    } catch (err) {

      console.warn("Error comprobando permisos:", err);

    }

  }


  /* ========================================================
     Obtener posición
     ======================================================== */

  navigator.geolocation.getCurrentPosition(

    async (pos) => {

      const lat =
        pos.coords.latitude;

      const lon =
        pos.coords.longitude;


      /* Mostrar inmediatamente la posición */

      inicializarOActualizarMapa(
        lat,
        lon
      );


      contenedor.innerHTML = `

        <p class="status-text">

          Buscando paradas y horarios cerca...

        </p>

      `;


      try {

        /* ==================================================
           Llamada al backend
           ================================================== */

        const config = obtenerConfig();

        const url =
          `${API_URL}?lat=${encodeURIComponent(lat)}` +
          `&lon=${encodeURIComponent(lon)}` +
          `&radio=${encodeURIComponent(config.radio)}` +
          `&max_paradas=${encodeURIComponent(config.maxParadas)}`;


        console.debug("Requesting backend:", url);

        const resp =
          await fetch(url);


        if (!resp.ok) {

          throw new Error(
            `HTTP ${resp.status}`
          );

        }


        const data =
          await resp.json();


        /* ==================================================
           Errores del backend
           ================================================== */

        if (data.error) {

          throw new Error(
            data.error
          );

        }


        /* ==================================================
           Mostrar resultados
           ================================================== */

        mostrarResultados(
          data,
          lat,
          lon
        );


      } catch (err) {

        console.error(
          "Error al consultar la API:",
          err
        );


        contenedor.innerHTML = `

          <p class="status-text error-text">

            ❌ Error al conectar con el servidor.

          </p>

        `;

      } finally {

        boton.disabled = false;

      }

    },


    /* ======================================================
       ERROR GPS
       ====================================================== */

    (error) => {

      console.error(
        "Error de GPS:",
        error
      );


      let mensaje =
        "No se pudo obtener tu ubicación.";



      if (error.code === error.PERMISSION_DENIED) {

        mensaje = "Has denegado el acceso a la ubicación.";

        // Mostrar modal con instrucciones para activar la ubicación
        mostrarModalActivarUbicacion();

      } else if (error.code === error.POSITION_UNAVAILABLE) {

        mensaje = "La ubicación no está disponible.";

      } else if (error.code === error.TIMEOUT) {

        mensaje = "Se agotó el tiempo esperando al GPS.";

      }


      contenedor.innerHTML = `

        <p class="status-text error-text">

          ❌ ${escaparHTML(mensaje)}

        </p>

      `;


      boton.disabled = false;

    },


    /* ======================================================
       OPCIONES GPS
       ====================================================== */

    {
      enableHighAccuracy: true,

      timeout: 10000,

      maximumAge: 0
    }

  );


  /* ========================================================
     Función auxiliar: solicitarPosicion()
     Llama a getCurrentPosition (extraer para reutilizar)
     ======================================================== */

  function solicitarPosicion() {

    boton.disabled = true;

    navigator.geolocation.getCurrentPosition(

      async (pos) => {

        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;

        inicializarOActualizarMapa(lat, lon);

        const contenedor = document.getElementById("contenido");

        contenedor.innerHTML = `\n\n        <p class="status-text">\n\n          Buscando paradas y horarios cerca...\n\n        </p>\n\n      `;

        try {

          const config = obtenerConfig();

          const url =
            `${API_URL}?lat=${encodeURIComponent(lat)}` +
            `&lon=${encodeURIComponent(lon)}` +
            `&radio=${encodeURIComponent(config.radio)}` +
            `&max_paradas=${encodeURIComponent(config.maxParadas)}`;

          console.debug("Requesting backend:", url);

          const resp = await fetch(url);

          if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
          }

          const data = await resp.json();

          if (data.error) {
            throw new Error(data.error);
          }

          mostrarResultados(data, lat, lon);

        } catch (err) {

          console.error("Error al consultar la API:", err);

          const cont = document.getElementById("contenido");

          cont.innerHTML = `\n\n          <p class="status-text error-text">\n\n            ❌ Error al conectar con el servidor.\n\n          </p>\n\n        `;

        } finally {

          boton.disabled = false;

        }

      },

      (error) => {

        console.error("Error de GPS:", error);

        const cont = document.getElementById("contenido");

        let mensaje = "No se pudo obtener tu ubicación.";

        if (error.code === error.PERMISSION_DENIED) {

          mensaje = "Has denegado el acceso a la ubicación.";

          mostrarModalActivarUbicacion();

        } else if (error.code === error.POSITION_UNAVAILABLE) {

          mensaje = "La ubicación no está disponible.";

        } else if (error.code === error.TIMEOUT) {

          mensaje = "Se agotó el tiempo esperando al GPS.";

        }

        cont.innerHTML = `\n\n        <p class="status-text error-text">\n\n          ❌ ${escaparHTML(mensaje)}\n\n        </p>\n\n      `;

        boton.disabled = false;

      },

      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }

    );

  }


  /* ========================================================
     Modal para instruir al usuario cómo activar la ubicación
     ======================================================== */

  function mostrarModalActivarUbicacion() {

    // Evitar duplicados
    if (document.getElementById("modal-activar-ubicacion")) {
      return;
    }

    const modal = document.createElement("div");
    modal.id = "modal-activar-ubicacion";
    modal.className = "modal";

    modal.innerHTML = `
      <div class="modal-contenido">
        <h2>Permiso de ubicación denegado</h2>
        <p>Para usar esta función debes activar el permiso de ubicación en tu navegador o dispositivo.</p>
        <ul>
          <li>En escritorio: abre la configuración del sitio (candado en la barra de direcciones) y permite "Ubicación".</li>
          <li>En Android/iOS: abre los ajustes del sistema para el navegador y activa el permiso de ubicación.</li>
        </ul>
        <div class="modal-botones">
          <button id="modal-cerrar" class="btn-cancelar">Cerrar</button>
          <button id="modal-abrir-ajustes" class="btn-guardar">Abrir ajustes del navegador</button>
          <button id="modal-reintentar" class="btn-guardar">Reintentar</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById("modal-cerrar").addEventListener("click", () => {
      modal.remove();
    });

    document.getElementById("modal-reintentar").addEventListener("click", () => {
      modal.remove();
      // Volver a intentar el flujo de permisos y posición
      buscarAutobuses();
    });

    document.getElementById("modal-abrir-ajustes").addEventListener("click", () => {
      const browser = detectarNavegador();
      const openTargets = obtenerUrlsAjustesUbicacion(browser, location.hostname);

      let opened = false;

      for (const url of openTargets) {
        try {
          const w = window.open(url, '_blank', 'noopener,noreferrer');
          if (w) {
            opened = true;
            break;
          }
        } catch (e) {
          console.warn('No se pudo abrir', url, e);
        }
      }

      if (!opened) {
        alert('No se pudo abrir automáticamente la configuración del navegador. Usa el candado de la barra de direcciones y activa la ubicación, o revisa la configuración de permisos del sitio.');
      }
    });

    function detectarNavegador() {
      const ua = navigator.userAgent.toLowerCase();

      if (ua.includes('brave')) return 'brave';
      if (ua.includes('edg')) return 'edge';
      if (ua.includes('firefox')) return 'firefox';
      if (ua.includes('safari') && !ua.includes('chrome')) return 'safari';
      if (ua.includes('chrome')) return 'chrome';

      return 'generic';
    }

    function obtenerUrlsAjustesUbicacion(browser, host) {
      const hostParam = encodeURIComponent(host);

      const urlsPorNavegador = {
        brave: [
          `brave://settings/content/siteDetails?search=${hostParam}`,
          'brave://settings/content/location',
          `chrome://settings/content/siteDetails?search=${hostParam}`,
          'chrome://settings/content/location',
          'https://support.brave.com/hc/en-us/articles/360034841871-How-do-I-change-site-settings-permissions-in-Brave'
        ],
        chrome: [
          `chrome://settings/content/siteDetails?search=${hostParam}`,
          'chrome://settings/content/location',
          'https://support.google.com/chrome/answer/142065'
        ],
        edge: [
          `edge://settings/content/siteDetails?search=${hostParam}`,
          'edge://settings/content/location',
          'https://support.microsoft.com/en-us/microsoft-edge/allow-or-block-location-access-for-sites-in-microsoft-edge-01c0d5f7-0ae9-5d7d-2d7f-5d5c8d2a0c82'
        ],
        firefox: [
          'about:preferences#privacy',
          'https://support.mozilla.org/en-US/kb/permission-request-messages-firefox'
        ],
        safari: [
          'x-apple.systempreferences:com.apple.preference.security?Privacy_LocationServices',
          'https://support.apple.com/guide/safari/allow-or-block-website-access-to-location-information-sfri34030/mac'
        ],
        generic: [
          'https://www.google.com/search?q=' + encodeURIComponent('how to enable location permissions in browser')
        ]
      };

      return urlsPorNavegador[browser] || urlsPorNavegador.generic;
    }

    // Cerrar modal al pulsar fuera del contenido
    modal.addEventListener('click', (ev) => {
      if (ev.target === modal) modal.remove();
    });

  }
}
