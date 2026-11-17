// Comprobación de versión / auto-reset: se carga lo primero en <head> (ver index.html).
(function () {
  var STORAGE_KEY = "gbt:lastVersion";
  var RELOAD_FLAG = "gbt:justReloaded";

  function limpiarRastrosAntiguos() {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.getRegistrations()
        .then(function (regs) {
          regs.forEach(function (reg) { reg.unregister(); });
        })
        .catch(function () {});
    }
    if (window.caches && caches.keys) {
      caches.keys()
        .then(function (keys) {
          keys.forEach(function (key) { caches.delete(key); });
        })
        .catch(function () {});
    }
  }

  fetch("/api/about", { cache: "no-store" })
    .then(function (resp) { return resp.ok ? resp.json() : null; })
    .then(function (data) {
      if (!data || !data.version) return;

      var versionActual = data.version;
      var versionGuardada = localStorage.getItem(STORAGE_KEY);

      if (versionGuardada && versionGuardada !== versionActual) {
        limpiarRastrosAntiguos();
        localStorage.setItem(STORAGE_KEY, versionActual);

        // Evita bucles de recarga infinitos si algo va mal.
        if (!sessionStorage.getItem(RELOAD_FLAG)) {
          sessionStorage.setItem(RELOAD_FLAG, "1");
          location.reload();
          return;
        }
      } else {
        localStorage.setItem(STORAGE_KEY, versionActual);
      }

      sessionStorage.removeItem(RELOAD_FLAG);
    })
    .catch(function () {
      // Si falla la comprobación, no bloqueamos la carga de la app.
    });
})();
