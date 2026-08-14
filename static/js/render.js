/**
 * Renderizado de resultados: tarjeta de parada, lista de autobuses.
 */

import { escaparHTML } from "./utils.js";
import { inicializarOActualizarMapa } from "./mapa.js";


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



export function mostrarResultados(
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
