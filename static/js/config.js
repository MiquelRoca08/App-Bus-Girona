/**
 * Configuración del usuario: radio de búsqueda y número máximo de
 * paradas a mostrar. Se persiste en localStorage para recordarla
 * entre visitas.
 */

const STORAGE_KEY = "proximo-bus:config";

const CONFIG_POR_DEFECTO = {
  radio: 100,
  maxParadas: 1,
};


export function obtenerConfig() {

  try {

    const guardado = localStorage.getItem(STORAGE_KEY);

    if (!guardado) {
      return { ...CONFIG_POR_DEFECTO };
    }

    const parseado = JSON.parse(guardado);

    const radio = Number(parseado.radio);
    const maxParadas = Number(parseado.maxParadas);

    return {
      radio: Number.isFinite(radio) && radio > 0
        ? radio
        : CONFIG_POR_DEFECTO.radio,
      maxParadas: Number.isFinite(maxParadas) && maxParadas > 0
        ? maxParadas
        : CONFIG_POR_DEFECTO.maxParadas,
    };

  } catch (err) {

    console.error("Error al leer la configuración guardada:", err);

    return { ...CONFIG_POR_DEFECTO };

  }

}


export function guardarConfig(config) {

  try {

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(config)
    );

  } catch (err) {

    console.error("Error al guardar la configuración:", err);

  }

}
