/**
 * Auto-actualización de horarios cada minuto en punto (segundo :00 del
 * reloj del dispositivo), igual que hace la web oficial de TMG.
 *
 * En vez de un setInterval(60000) simple (que se desincroniza del
 * reloj según el momento exacto en que se cargó la página), se calcula
 * cuánto falta hasta el próximo :00 y se dispara un setTimeout hasta
 * ahí; a partir de ese primer disparo, se usa setInterval(60000), que
 * en la práctica se mantiene alineado al minuto salvo pequeñas derivas
 * (por eso se re-sincroniza en cada ciclo, ver más abajo).
 */

let intervaloId = null;
let timeoutId = null;

/**
 * Milisegundos que faltan hasta el próximo segundo :00 del reloj.
 */
function msHastaProximoMinuto() {
  const ahora = new Date();
  const ms = ahora.getMilliseconds();
  const s = ahora.getSeconds();
  return (60 - s) * 1000 - ms;
}

/**
 * Arranca el ciclo de auto-actualización. `callback` se invoca una vez
 * al llegar cada :00 del reloj. Si ya había un ciclo en marcha, se
 * detiene antes de arrancar uno nuevo (evita duplicar temporizadores).
 */
export function iniciarAutoActualizacion(callback) {

  detenerAutoActualizacion();

  function programarCiclo() {

    timeoutId = setTimeout(() => {

      callback();

      // A partir de aquí, disparo cada 60s. Como los navegadores no
      // garantizan precisión absoluta en temporizadores en segundo
      // plano (pestañas no activas, throttling), se re-sincroniza al
      // segundo :00 en cada vuelta en lugar de confiar en que 60
      // intervalos de 60000ms sigan alineados indefinidamente.
      intervaloId = setInterval(() => {
        callback();
      }, 60000);

    }, msHastaProximoMinuto());

  }

  programarCiclo();

}

/**
 * Detiene cualquier ciclo de auto-actualización en marcha.
 */
export function detenerAutoActualizacion() {

  if (timeoutId !== null) {
    clearTimeout(timeoutId);
    timeoutId = null;
  }

  if (intervaloId !== null) {
    clearInterval(intervaloId);
    intervaloId = null;
  }

}
