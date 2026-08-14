/**
 * Gestión del minimapa Leaflet: inicialización, marcador de usuario,
 * marcador de parada, y recentrado.
 */

import { escaparHTML } from "./utils.js";

let map = null;
let userMarker = null;
let stopMarker = null;
let lastUserCoords = null;


export function recentrarUbicacion() {

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



export function inicializarOActualizarMapa(
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
