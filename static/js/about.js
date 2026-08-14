import { escaparHTML } from "./utils.js";

export async function abrirAbout() {
  const modal = document.getElementById("modal-about");
  const content = document.getElementById("about-content");
  const versionEl = document.getElementById("app-version");

  modal.classList.remove("oculto");

  try {
    const resp = await fetch("/api/about");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    versionEl.textContent = `Versión: ${data.version}`;

    content.innerHTML = `
      <p><strong>Versión:</strong> ${escaparHTML(data.version)}</p>
      <p><strong>Paradas GTFS:</strong> ${escaparHTML(String(data.num_paradas))}</p>
      <p><strong>Rutas GTFS:</strong> ${escaparHTML(String(data.num_rutas))}</p>
      <p><a href="https://github.com/MiquelRoca08/Girona-Bus-Tracker" target="_blank" rel="noopener">Repositorio en GitHub</a></p>
      `;
  } catch (err) {
    versionEl.textContent = `Versión: —`;
    content.innerHTML = `<p>Error al cargar información.</p>`;
    console.error("Error fetching /api/about:", err);
  }
}

export function cerrarAbout() {
  const modal = document.getElementById("modal-about");
  modal.classList.add("oculto");
}


export async function actualizarVersion() {
  const versionEl = document.getElementById("app-version");
  if (!versionEl) return;

  try {
    const resp = await fetch("/api/about");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    versionEl.textContent = `Versión: ${data.version}`;
  } catch (err) {
    console.debug("No se pudo cargar la versión:", err);
  }
}
