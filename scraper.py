# scraper.py
import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

import config
from redis_utils import get_redis_client, store_data_in_redis

LI_JOB_URL = "https://www.linkedin.com/jobs/search/"

# User-Agent básico para evitar bloqueos rápidos (no es garantía, pero ayuda)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def transform_obj_to_params(obj):
    """Función equivalente a la que usabas en el notebook (ya no es imprescindible)."""
    return "&".join([f"{key}={value}" for key, value in obj.items()])


def get_linkedin_jobs(keywords="", experience_levels="1,2,3,4,5", max_pages=5):
    """
    Recupera trabajos publicados HOY en LinkedIn (Perú) usando scraping.
    Devuelve una lista de diccionarios.
    """

    params = {
        "keywords": keywords,
        "f_E": experience_levels,
        "geoId": config.LINKEDIN_GEO_ID_PERU,
        "f_TPR": "r86400",  # últimas 24h
    }

    jobs_data = []
    today = datetime.now().date()

    for page in range(max_pages):
        params["start"] = page * 25  # 25 resultados por página en LinkedIn
        resp = requests.get(LI_JOB_URL, params=params, headers=HEADERS, timeout=15)

        if resp.status_code != 200:
            # si LinkedIn bloquea o falla, pasamos a la siguiente página
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = soup.select(".jobs-search__results-list li")

        for job in jobs:
            div = job.select_one("div")
            if not div or "data-entity-urn" not in div.attrs:
                continue

            # Fecha de publicación
            fecha_creacion_elem = job.select_one(".job-search-card__listdate")
            fecha_creacion = None
            if (
                fecha_creacion_elem
                and "datetime" in getattr(fecha_creacion_elem, "attrs", {})
            ):
                try:
                    fecha_creacion = fecha_creacion_elem["datetime"]
                    fecha_publicacion = datetime.fromisoformat(
                        fecha_creacion
                    ).date()
                    # Filtramos solo los trabajos de HOY
                    if fecha_publicacion != today:
                        continue
                except Exception:
                    pass

            empresa_elem = job.select_one(".hidden-nested-link")
            empresa_nombre = (
                empresa_elem.get_text(strip=True) if empresa_elem else "Confidential"
            )

            puesto_elem = job.select_one("h3")
            puesto = (
                re.sub(r"\s+", " ", unidecode(puesto_elem.get_text()))
                if puesto_elem
                else ""
            ).strip()

            location_elem = job.select_one(".job-search-card__location")
            lugar = (
                re.sub(r"\s+", " ", unidecode(location_elem.get_text()))
                if location_elem
                else ""
            ).strip()

            tiempo_relativo = (
                re.sub(
                    r"\s+",
                    " ",
                    unidecode(fecha_creacion_elem.get_text()),
                ).strip()
                if fecha_creacion_elem
                else None
            )

            # Logo
            logo_elem = job.select_one(".search-entity-media img")
            logo_url = None
            if logo_elem is not None:
                if "data-delayed-url" in logo_elem.attrs:
                    logo_url = logo_elem["data-delayed-url"]
                elif "src" in logo_elem.attrs:
                    logo_url = logo_elem["src"]

            job_link_elem = job.select_one("a")
            enlace = job_link_elem["href"] if job_link_elem and "href" in job_link_elem.attrs else ""

            # Normalizamos la info en un dict
            job_data = {
                "urn": div["data-entity-urn"],
                "id": div["data-entity-urn"].split(":")[-1],
                "puesto": puesto,
                "enlace": enlace,
                "lugar": lugar,
                "fecha_creacion": fecha_creacion,
                "tiempo_relativo": tiempo_relativo,
                "empresa": {
                    "logo": logo_url,
                    "enlace_empresa": (
                        empresa_elem["href"].split("?")[0]
                        if empresa_elem and "href" in empresa_elem.attrs
                        else None
                    ),
                    "nombre": empresa_nombre,
                },
            }

            jobs_data.append(job_data)

    return jobs_data


def get_job_urls(jobs_data):
    """Devuelve solo la lista de URLs de los trabajos."""
    return [job["enlace"] for job in jobs_data if job.get("enlace")]


def main():
    client = get_redis_client()
    jobs_data = get_linkedin_jobs(keywords="", max_pages=5)

    # misma clave que en tu notebook: "scraper_4_data"
    key = store_data_in_redis("scraper_4", jobs_data, client=client)

    print(f"Datos guardados en Redis con la clave '{key}'")
    print(f"Total de trabajos encontrados hoy: {len(jobs_data)}\n")

    print("Ejemplo (primeros 3 trabajos):")
    print(json.dumps(jobs_data[:3], indent=2, ensure_ascii=False))

    print("\nURLs de los trabajos encontrados hoy:")
    for url in get_job_urls(jobs_data):
        print(url)


if __name__ == "__main__":
    main()
