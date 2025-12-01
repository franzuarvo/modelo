# redis_utils.py
import json
from datetime import datetime

import redis
import config


def get_redis_client():
    """Devuelve un cliente de Redis listo para usar."""

    # 👉 Si tenemos REDIS_URL (Upstash), usamos eso
    if config.REDIS_URL:
        return redis.from_url(
            config.REDIS_URL,
            decode_responses=True,
        )

    # 👉 Fallback: Redis clásico por host/puerto (por ejemplo en local)
    return redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        password=config.REDIS_PASSWORD,
        decode_responses=True,
    )


def store_data_in_redis(scraper_name, data, client=None):
    """
    Guarda datos en Redis con formato:

    clave:  "<scraper_name}_data"
    valor:  {
        "timestamp": "...",
        "data": [...]
    }
    """
    if client is None:
        client = get_redis_client()

    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data,
    }
    key = f"{scraper_name}_data"
    client.set(key, json.dumps(payload, ensure_ascii=False))
    return key


def load_data_from_redis(scraper_name, client=None):
    """
    Carga y devuelve la lista de datos para un scraper (o [] si no hay nada).
    """
    if client is None:
        client = get_redis_client()

    key = f"{scraper_name}_data"
    raw = client.get(key)
    if not raw:
        return []

    try:
        obj = json.loads(raw)
        # si el formato es {"timestamp": ..., "data": [...]}
        if isinstance(obj, dict) and "data" in obj:
            return obj["data"]
        # si por alguna razón solo guardaste una lista
        if isinstance(obj, list):
            return obj
    except Exception:
        pass

    return []
