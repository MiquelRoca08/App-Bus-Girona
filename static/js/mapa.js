/**
 * Gestión del minimapa Leaflet: inicialización, marcador de usuario,
 * marcador de parada, y recentrado.
 */

import { escaparHTML } from "./utils.js";

let map = null;
let userMarker = null;
let stopMarkers = [];
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
  paradas = []
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
     MARCADORES DE LAS PARADAS
     ======================================================== */

  /* Limpiar marcadores de paradas anteriores */

  stopMarkers.forEach((marker) => {
    map.removeLayer(marker);
  });

  stopMarkers = [];


  const paradasValidas = paradas.filter((parada) =>
    parada &&
    parada.stop_lat !== null &&
    parada.stop_lat !== undefined &&
    parada.stop_lon !== null &&
    parada.stop_lon !== undefined &&
    !Number.isNaN(Number(parada.stop_lat)) &&
    !Number.isNaN(Number(parada.stop_lon))
  );


  if (paradasValidas.length > 0) {

    const puntosEncuadre = [
      lastUserCoords
    ];


    paradasValidas.forEach((parada) => {

      const stopCoords = [
        Number(parada.stop_lat),
        Number(parada.stop_lon)
      ];

      const marker = L.marker(
        stopCoords
      )
      .addTo(map)
      .bindPopup(
        `🚏 ${escaparHTML(parada.stop_name)}`
      );

      stopMarkers.push(marker);

      puntosEncuadre.push(stopCoords);

    });


    /* Encuadrar usuario y todas las paradas */

    const bounds = L.latLngBounds(
      puntosEncuadre
    );


    map.fitBounds(
      bounds,
      {
        padding: [30, 30]
      }
    );

  } else {

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
