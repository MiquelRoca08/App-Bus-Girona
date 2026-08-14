/**
 * Panel de configuración (⚙️): abre y cierra el modal, valida los
 * inputs de radio y máximo de paradas, y guarda los cambios.
 */

import { obtenerConfig, guardarConfig } from "./config.js";

const RADIO_MIN = 10;
const RADIO_MAX = 2000;
const MAX_PARADAS_MIN = 1;
const MAX_PARADAS_MAX = 20;


export function abrirPanelConfig() {

  const modal =
    document.getElementById("modal-config");

  const inputRadio =
    document.getElementById("input-radio");

  const inputMaxParadas =
    document.getElementById("input-max-paradas");

  const config = obtenerConfig();

  inputRadio.value = config.radio;
  inputMaxParadas.value = config.maxParadas;

  modal.classList.remove("oculto");

}


export function cerrarPanelConfig() {

  const modal =
    document.getElementById("modal-config");

  modal.classList.add("oculto");

}


export function guardarPanelConfig() {

  const inputRadio =
    document.getElementById("input-radio");

  const inputMaxParadas =
    document.getElementById("input-max-paradas");

  let radio = Number(inputRadio.value);
  let maxParadas = Number(inputMaxParadas.value);

  if (!Number.isFinite(radio)) {
    radio = RADIO_MIN;
  }

  if (!Number.isFinite(maxParadas)) {
    maxParadas = MAX_PARADAS_MIN;
  }

  radio = Math.min(
    Math.max(radio, RADIO_MIN),
    RADIO_MAX
  );

  maxParadas = Math.min(
    Math.max(Math.round(maxParadas), MAX_PARADAS_MIN),
    MAX_PARADAS_MAX
  );

  guardarConfig({ radio, maxParadas });

  cerrarPanelConfig();

  return { radio, maxParadas };

}
