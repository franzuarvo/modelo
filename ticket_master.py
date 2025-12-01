# ticket_master.py
import json
import requests

import config
from redis_utils import get_redis_client, store_data_in_redis

# Token de Eventbrite (evita fallo si no existe en config)
EVENTBRITE_TOKEN = getattr(config, "EVENTBRITE_TOKEN", "")


def normalize_event(source, title, start, city, url, raw=None, description=None):
    return {
        "source": source,
        "title": title or "",
        "start": start,
        "city": city or "",
        "url": url or "",
        "description": description or "",
        "raw": raw or {},
    }


# --------------------------------------
# Ticketmaster: eventos en Lima (Perú)
# --------------------------------------
def fetch_events_ticketmaster_lima(limit=20):
    """
    Trae eventos desde Ticketmaster para Perú, filtrando por Lima.
    """
    if not config.TICKETMASTER_API_KEY:
        print("⚠️ TICKETMASTER_API_KEY no configurado. Saltando Ticketmaster.")
        return []

    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": config.TICKETMASTER_API_KEY,
        "countryCode": "PE",
        "city": "Lima",
        "size": limit,
        "sort": "date,asc",
    }

    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    events = []
    for e in data.get("_embedded", {}).get("events", []):
        title = e.get("name", "")

        dates = e.get("dates", {}) or {}
        start = dates.get("start", {}).get("dateTime") or dates.get("start", {}).get(
            "localDate"
        )

        venues = e.get("_embedded", {}).get("venues", []) if "_embedded" in e else []
        city = ""
        if venues:
            city = (venues[0].get("city") or {}).get("name", "")

        url_evt = e.get("url", "")

        events.append(
            normalize_event(
                source="ticketmaster",
                title=title,
                start=start,
                city=city,
                url=url_evt,
                raw=e,
            )
        )

    return events


# --------------------------------------
# Eventbrite: eventos en Lima (Perú)
# --------------------------------------
def fetch_events_eventbrite_lima(limit=20):
    """
    Trae eventos públicos desde Eventbrite para Lima, Perú.
    """
    if not EVENTBRITE_TOKEN:
        print("⚠️ EVENTBRITE_TOKEN no configurado. Saltando Eventbrite.")
        return []

    url = "https://www.eventbriteapi.com/v3/events/search/"

    headers = {
        "Authorization": f"Bearer {EVENTBRITE_TOKEN}",
    }

    params = {
        "location.address": "Lima, Peru",
        "expand": "venue",
        "page_size": limit,
    }

    resp = requests.get(url, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    events = []
    for e in data.get("events", []):
        name_obj = e.get("name") or {}
        title = name_obj.get("text", "")

        start_obj = e.get("start") or {}
        start = start_obj.get("local")  # fecha/hora local

        url_evt = e.get("url", "")

        venue = e.get("venue") or {}
        address = venue.get("address") or {}
        city = address.get("city") or ""

        description_obj = e.get("description") or {}
        description = description_obj.get("text", "")

        events.append(
            normalize_event(
                source="eventbrite",
                title=title,
                start=start,
                city=city,
                url=url_evt,
                raw=e,
                description=description,
            )
        )

    return events


# --------------------------------------
# RapidAPI: Real-Time Events Search (Perú)
# --------------------------------------
def fetch_events_rapidapi_peru(city="Lima", country="Peru", max_results=50):
    """
    Obtiene eventos usando Real-Time Events Search (RapidAPI).
    """
    if not config.RAPIDAPI_KEY:
        print("⚠️ RAPIDAPI_KEY no configurado. Saltando RapidAPI.")
        return []

    url = "https://real-time-events-search.p.rapidapi.com/search-events"

    querystring = {
        "query": f"Events in {city} {country}",
        "limit": max_results,
    }

    headers = {
        "X-RapidAPI-Key": config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "real-time-events-search.p.rapidapi.com",
    }

    resp = requests.get(url, params=querystring, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    parsed = []
    for e in data.get("data", []):
        parsed.append(
            normalize_event(
                source=e.get("source", "rapidapi"),
                title=e.get("title"),
                start=e.get("start_time"),
                city=e.get("location") or "",
                url=e.get("url"),
                raw=e,
                description=e.get("description"),
            )
        )

    return parsed


def run_and_store_events():
    """
    Ejecuta los scrapers de eventos, une los resultados
    y los guarda en Redis bajo la clave 'events_peru_data'.
    """
    client = get_redis_client()

    events = []
    events += fetch_events_ticketmaster_lima(limit=50)
    events += fetch_events_eventbrite_lima(limit=50)
    events += fetch_events_rapidapi_peru(city="Lima", country="Peru", max_results=50)

    key = store_data_in_redis("events_peru", events, client=client)

    print(f"Datos de eventos guardados en Redis con la clave '{key}'")
    print(f"Total de eventos encontrados: {len(events)}\n")

    print("Ejemplo (primeros 3 eventos):")
    print(json.dumps(events[:3], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run_and_store_events()
