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


  // intentar usar un icono SVG para la línea (por ejemplo line-1.svg)
  const lineaId = linea.replace(/^L/i, "").trim();
  const iconPath = `/static/assets/line-icons/line-${lineaId}.svg`;

  return `

    <div class="bus-item">

      <span class="badge-linea">
        <img src="${iconPath}" alt="${lineaId}" class="badge-icon" onerror="(function(){this.style.display='none'; var s=this.nextElementSibling; if(s) s.style.display='inline-block'; }).call(this)"/>
        <span class="badge-text">${linea}</span>
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



function generarHTMLParada(entradaParada) {

  const parada =
    entradaParada.parada;


  const autobuses =
    Array.isArray(
      entradaParada.proximos_autobuses
    )
      ? entradaParada.proximos_autobuses
      : [];


  /* ========================================================
     Determinar fuente
     ======================================================== */

  const tiempoReal =
    entradaParada.tiempo_real_disponible === true ||
    entradaParada.fuente_horarios === "tmg_tiempo_real";


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
     Tarjeta de la parada
     ======================================================== */

  return `

    <div class="parada-card">

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

  if (
    !data.encontrada ||
    !Array.isArray(data.paradas) ||
    data.paradas.length === 0
  ) {

    contenedor.innerHTML = `

      <p class="status-text">

        ${escaparHTML(
          data.mensaje ||
          "No se han encontrado paradas cercanas."
        )}

      </p>

    `;

    inicializarOActualizarMapa(
      lat,
      lon
    );

    return;

  }


  /* Actualizar mapa con todas las paradas encontradas */

  inicializarOActualizarMapa(

    lat,

    lon,

    data.paradas.map((p) => p.parada)

  );


  /* ========================================================
     Renderizar una tarjeta por parada
     ======================================================== */

  contenedor.innerHTML = data.paradas
    .map(generarHTMLParada)
    .join("");

}
