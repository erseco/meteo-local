# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public city-centre coordinates; no private station or home location."""
from zoneinfo import ZoneInfo

VERSION = "0.3.1"
NAME = "Las Palmas de Gran Canaria"
COORDINATES = (28.124, -15.436)
TIMEZONE = "Atlantic/Canary"
ZONE = ZoneInfo(TIMEZONE)
ALERT_AREA = "Norte de Gran Canaria"
AEMET = "https://www.aemet.es/es/eltiempo/prediccion/municipios/palmas-de-gran-canaria-las-id35016"
AEMET_ALERTS = "https://www.aemet.es/es/eltiempo/prediccion/avisos?l=659001"
REPOSITORY = "https://github.com/erseco/meteo-local"
UNAVAILABLE = {
    "observaciones": "AEMET y METAR disponibles según antigüedad; cada estación conserva su ubicación y sus unidades.",
    "radar": "Radar y avisos de llegada de lluvia no disponibles; consulte AEMET.",
    "planes": "Alertas de Protección Civil de Canarias no integradas.",
    "riera": "El modelo de crecidas de Sant Cugat no es aplicable a los barrancos de Gran Canaria.",
    "trens": "Las Palmas no tiene los servicios ferroviarios de Montflorit. Guaguas no integrado.",
    "transit": "Incidencias de tráfico locales no integradas.",
    "llum": "Cortes de suministro locales no integrados.",
    "pollen": "Polen local no disponible; no se utiliza Bellaterra.",
    "entorn": "Incendios y restricciones locales no integrados.",
    "aprenentatge": "Historial local en recogida. Las correcciones requieren validación temporal y suficiente muestra; no se usan datos de Montflorit.",
    "notificaciones": "Telegram y notificaciones push requieren un servicio y credenciales propios.",
}
