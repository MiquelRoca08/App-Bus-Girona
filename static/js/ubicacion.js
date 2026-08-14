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


      if (
        error.code ===
        error.PERMISSION_DENIED
      ) {

        mensaje =
          "Has denegado el acceso a la ubicación.";

      } else if (
        error.code ===
        error.POSITION_UNAVAILABLE
      ) {

        mensaje =
          "La ubicación no está disponible.";

      } else if (
        error.code ===
        error.TIMEOUT
      ) {

        mensaje =
          "Se agotó el tiempo esperando al GPS.";

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

}
