"""Parseo del HTML/JSON que devuelve AppBus (TMG) para extraer llegadas."""

import html
import re
from datetime import datetime, timedelta
from html.parser import HTMLParser

from app.config import TZ_MADRID


class _TextoHTMLParser(HTMLParser):
    """Extrae únicamente texto visible de un fragmento HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []
        self._ocultar = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript"}:
            self._ocultar += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript"} and self._ocultar:
            self._ocultar -= 1

    def handle_data(self, data):
        if not self._ocultar and data.strip():
            self.partes.append(data)


def _extraer_texto_contingut(contingut):
    """Convierte el HTML de 'contingut' a texto visible de forma segura."""
    if not contingut:
        return ""

    texto = html.unescape(str(contingut))
    parser = _TextoHTMLParser()

    try:
        parser.feed(texto)
        texto = " ".join(parser.partes)
    except Exception:
        # Fallback para HTML incompleto.
        texto = re.sub(r"<[^>]+>", " ", texto)

    return re.sub(r"\s+", " ", texto).strip()


def _extraer_contingut(payload):
    """Obtiene contingut incluso si AppBus cambia ligeramente la envoltura."""
    if isinstance(payload, dict):
        for clave in ("contingut", "contenido", "content", "html", "result"):
            valor = payload.get(clave)
            if isinstance(valor, str):
                return valor

        # Algunas respuestas podrían envolver el resultado en otro objeto.
        for valor in payload.values():
            if isinstance(valor, dict):
                resultado = _extraer_contingut(valor)
                if resultado:
                    return resultado

    elif isinstance(payload, str):
        return payload

    return ""


def _parsear_contingut_tmg(payload):
    """Extrae llegadas de AppBus.

    Admite:
      - '5 min', '12 minuts', etc.
      - '5m' / '5 min.'
      - '5\'' como abreviatura de minutos
      - horas absolutas HH:MM

    Devuelve una lista ordenada y sin duplicados.
    """
    contingut = _extraer_contingut(payload)
    texto = _extraer_texto_contingut(contingut)

    if not texto:
        return []

    texto_lower = texto.lower()
    if "sense informaci" in texto_lower or "sin información" in texto_lower:
        return []

    resultados = []

    # Tiempos relativos.
    patrones_minutos = [
        r"(?<!\d)(\d{1,3})\s*(?:min|mins|minut|minuts)\.?\b",
        r"(?<!\d)(\d{1,3})\s*m\b",
        r"(?<!\d)(\d{1,3})\s*[′']\b",
    ]

    for patron in patrones_minutos:
        for match in re.finditer(patron, texto, re.I):
            minutos = int(match.group(1))
            if minutos > 240:
                continue

            llegada = datetime.now(TZ_MADRID) + timedelta(minutes=minutos)
            resultados.append({
                "minutos": minutos,
                "hora": llegada.strftime("%H:%M"),
            })

    # Horas absolutas.
    for match in re.finditer(
        r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)",
        texto,
    ):
        hora = f"{int(match.group(1)):02d}:{match.group(2)}"
        resultados.append({
            "minutos": None,
            "hora": hora,
        })

    # Elimina duplicados y ordena por hora/minutos.
    unicos = []
    vistos = set()

    for item in resultados:
        clave = (item["hora"], item["minutos"])
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(item)

    unicos.sort(
        key=lambda item: (
            item["minutos"] is None,
            item["minutos"] if item["minutos"] is not None else 9999,
            item["hora"],
        )
    )

    return unicos
