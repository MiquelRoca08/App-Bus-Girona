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

      <img src="${iconPath}" alt="${lineaId}" class="badge-icon" onerror="this.style.display='none'"/>

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

      <div class="parada-links" id="links-parada-${escaparHTML(parada.stop_id)}">
        <a href="https://web2.girona.cat/appbus/cat/parada?codi=${escaparHTML(parada.stop_id)}" target="_blank" class="link-oficial">
          🌐 Ver parada en TMG
        </a>
      </div>

    </div>

  `;

}


/**
 * Comprueba si existe un PDF para la parada y, si es así, añade el
 * enlace correspondiente dentro de la tarjeta ya renderizada.
 * Se hace de forma asíncrona y "best effort": si la comprobación falla
 * (red, 404, etc.) simplemente no se muestra el enlace.
 */
async function anadirEnlacePdfSiExiste(stopId) {

  try {

    const respuesta = await fetch(
      `/api/parada/${encodeURIComponent(stopId)}/tiene-pdf`
    );

    if (!respuesta.ok) {
      return;
    }

    const datos = await respuesta.json();

    if (!datos.tiene_pdf) {
      return;
    }

    const contenedorLinks = document.getElementById(
      `links-parada-${stopId}`
    );

    if (!contenedorLinks) {
      return;
    }

    const enlacePdf = document.createElement("a");
    enlacePdf.href = `/api/parada/${encodeURIComponent(stopId)}/pdf`;
    enlacePdf.target = "_blank";
    enlacePdf.className = "link-pdf";
    enlacePdf.textContent = "📄 Ver PDF de la parada";

    contenedorLinks.appendChild(enlacePdf);

  } catch (error) {

    // Fallo de red u otro error: no mostramos el enlace, sin romper la UI.
    console.warn(
      `No se pudo comprobar el PDF de la parada ${stopId}:`,
      error
    );

  }

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


  /* ========================================================
     Comprobar y añadir enlaces a PDF por parada (asíncrono,
     no bloquea el pintado de las tarjetas)
     ======================================================== */

  data.paradas.forEach((entradaParada) => {

    anadirEnlacePdfSiExiste(
      entradaParada.parada.stop_id
    );

  });

}
