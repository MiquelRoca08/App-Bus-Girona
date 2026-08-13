/* ============================================================
       CONFIGURACIÓN
       ============================================================ */

    const API_URL = "/api/proxima-parada";

    const RADIO_BUSQUEDA = 100;

    let map = null;

    let userMarker = null;

    let stopMarker = null;

    let lastUserCoords = null;


    /* ============================================================
       UTILIDADES
       ============================================================ */

    function escaparHTML(texto) {

      if (texto === null || texto === undefined) {
        return "";
      }

      const div = document.createElement("div");

      div.textContent = String(texto);

      return div.innerHTML;
    }


    /* ============================================================
       BOTÓN RECENTRAR
       ============================================================ */

    function recentrarUbicacion() {

      if (map && lastUserCoords) {

        map.flyTo(
          lastUserCoords,
          16,
          {
            animate: true,
            duration: 1.0
          }
        );

      } else {

        alert("Esperando señal GPS...");

      }
    }


    /* ============================================================
       MAPA
       ============================================================ */

    function inicializarOActualizarMapa(
      userLat,
      userLon,
      stopLat = null,
      stopLon = null,
      stopName = ""
    ) {

      lastUserCoords = [
        userLat,
        userLon
      ];


      /* Crear mapa si todavía no existe */

      if (!map) {

        map = L.map("map-card", {

          zoomControl: false,

          attributionControl: false

        }).setView(
          lastUserCoords,
          16
        );


        L.tileLayer(
          "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
          {
            maxZoom: 19
          }
        ).addTo(map);

      }


      /* ========================================================
         MARCADOR DEL USUARIO
         ======================================================== */

      if (userMarker) {

        userMarker.setLatLng(
          lastUserCoords
        );

      } else {

        userMarker = L.circleMarker(
          lastUserCoords,
          {
            radius: 8,

            fillColor: "#2563eb",

            color: "#ffffff",

            weight: 2,

            opacity: 1,

            fillOpacity: 1
          }
        )
        .addTo(map)
        .bindPopup("📍 Tu ubicación");

      }


      /* ========================================================
         MARCADOR DE LA PARADA
         ======================================================== */

      if (
        stopLat !== null &&
        stopLon !== null &&
        !Number.isNaN(Number(stopLat)) &&
        !Number.isNaN(Number(stopLon))
      ) {

        const stopCoords = [
          Number(stopLat),
          Number(stopLon)
        ];


        if (stopMarker) {

          stopMarker.setLatLng(
            stopCoords
          );

        } else {

          stopMarker = L.marker(
            stopCoords
          ).addTo(map);

        }


        stopMarker.bindPopup(
          `🚏 ${escaparHTML(stopName)}`
        );


        /* Encuadrar usuario y parada */

        const bounds = L.latLngBounds([
          lastUserCoords,
          stopCoords
        ]);


        map.fitBounds(
          bounds,
          {
            padding: [30, 30]
          }
        );

      } else {

        if (stopMarker) {

          map.removeLayer(
            stopMarker
          );

          stopMarker = null;

        }


        map.setView(
          lastUserCoords,
          16
        );

      }


      /* Leaflet necesita recalcular el tamaño */

      setTimeout(
        () => map.invalidateSize(),
        100
      );

    }


    /* ============================================================
       RENDERIZADO DE AUTOBUSES
       ============================================================ */

    function generarHTMLAutobus(bus) {

      const linea = escaparHTML(
        bus.linea || "Bus"
      );


      const destino = escaparHTML(
        bus.destino || "Sin destino"
      );


      const hora = escaparHTML(
        bus.hora || "--:--"
      );


      let minutosHTML = "";

      if (
        bus.tiempo_real === true &&
        bus.minutos !== null &&
        bus.minutos !== undefined
      ) {

        const minutos = Number(
          bus.minutos
        );


        if (!Number.isNaN(minutos)) {

          let textoMinutos;

          if (minutos <= 0) {

            textoMinutos = "Ahora";

          } else if (minutos === 1) {

            textoMinutos = "1 min";

          } else {

            textoMinutos = `${minutos} min`;

          }


          minutosHTML = `
            <span class="bus-minutos">
              ${textoMinutos}
            </span>
          `;

        }

      }


      return `

        <div class="bus-item">

          <span class="badge-linea">
            ${linea}
          </span>

          <span class="bus-destino">
            ${destino}
          </span>

          <span class="bus-hora-container">

            <span class="bus-hora">
              ${hora}
            </span>

            ${minutosHTML}

          </span>

        </div>

      `;

    }


    /* ============================================================
       MOSTRAR RESULTADOS
       ============================================================ */

    function mostrarResultados(
      data,
      lat,
      lon
    ) {

      const contenedor =
        document.getElementById(
          "contenido"
        );


      /* ========================================================
         Comprobar parada
         ======================================================== */

      if (!data.encontrada) {

        contenedor.innerHTML = `

          <p class="status-text">

            ${escaparHTML(
              data.mensaje ||
              "No se han encontrado paradas cercanas."
            )}

          </p>

        `;

        return;

      }


      const parada =
        data.parada;


      const autobuses =
        Array.isArray(
          data.proximos_autobuses
        )
          ? data.proximos_autobuses
          : [];


      /* Actualizar mapa */

      inicializarOActualizarMapa(

        lat,

        lon,

        parada.stop_lat,

        parada.stop_lon,

        parada.stop_name

      );


      /* ========================================================
         Determinar fuente
         ======================================================== */

      const tiempoReal =
        data.tiempo_real_disponible === true ||
        data.fuente_horarios === "tmg_tiempo_real";


      let fuenteHTML;


      if (tiempoReal) {

        fuenteHTML = `

          <div class="fuente-horarios fuente-tiempo-real">

            🟢

            <span>
              Horarios en tiempo real
            </span>

          </div>

        `;

      } else {

        fuenteHTML = `

          <div class="fuente-horarios fuente-programada">

            🕒

            <span>
              Horarios programados
            </span>

          </div>

        `;

      }


      /* ========================================================
         Lista de autobuses
         ======================================================== */

      let htmlBuses = "";


      if (autobuses.length > 0) {

        htmlBuses = autobuses
          .map(generarHTMLAutobus)
          .join("");

      } else {

        htmlBuses = `

          <p class="status-text">

            No hay autobuses próximos disponibles.

          </p>

        `;

      }


      /* ========================================================
         Renderizar tarjeta
         ======================================================== */

      contenedor.innerHTML = `

        <div class="parada-header">

          <div class="parada-nombre">

            ${escaparHTML(parada.stop_id)} | ${escaparHTML(
              parada.stop_name
            )}

          </div>

          <div class="parada-distancia">

            📍 a
            ${escaparHTML(
              parada.distancia_m
            )}
            metros de ti

          </div>

        </div>


        ${fuenteHTML}


        <div class="bus-list">

          ${htmlBuses}

        </div>

      `;

    }


    /* ============================================================
       BUSCAR AUTOBUSES
       ============================================================ */

    function buscarAutobuses() {

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

            const url =
              `${API_URL}?lat=${encodeURIComponent(lat)}` +
              `&lon=${encodeURIComponent(lon)}` +
              `&radio=${RADIO_BUSQUEDA}`;


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


    /* ============================================================
       INICIO
       ============================================================ */

    window.addEventListener(
      "load",
      buscarAutobuses
    );