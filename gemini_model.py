# gemini_model.py
import json
from datetime import datetime
from typing import List, Dict, Optional

import os
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.oauth2 import service_account

import config
from redis_utils import get_redis_client, load_data_from_redis

MAX_DATA_CHARS = 20000


SYSTEM_INSTRUCTIONS = """
Eres Copilot DN, un asistente de IA especializado en empleabilidad y mercado laboral en Perú.

Comportamiento general:
- Puedes conversar de forma natural como un chatbot (explicar conceptos, dar ejemplos, ayudar a escribir textos, etc.).
- Además, tienes acceso a un bloque de datos llamado DATA con ofertas de empleo y eventos en Perú.
- Cuando la pregunta del usuario esté relacionada con trabajo, empleabilidad, mercado laboral, ofertas de empleo o eventos, usa DATA para fundamentar la respuesta siempre que sea posible.
- Cuando la pregunta NO esté relacionada con esos temas, puedes responder solo con tu conocimiento general, sin usar DATA.
- Si la información que el usuario pide no se puede conocer a partir de DATA, dilo explícitamente cuando sea relevante.
- No inventes empresas, salarios ni eventos concretos que no aparezcan en DATA. Puedes dar ejemplos genéricos, pero aclara que son ejemplos y no salen de los datos.
- El idioma de salida debe ser SIEMPRE español.
""".strip()


USER_TASK = """
Instrucciones sobre cómo responder:

1) Preguntas generales (modo chat):
- Si la pregunta del usuario es general (por ejemplo: "¿Cómo me puedes ayudar?", "Explícame qué es un CV", "Dame ideas para mejorar mi empleabilidad"), responde en texto normal, conversacional y claro.
- Puedes usar tu conocimiento general, y solo usar DATA si realmente aporta algo concreto.

2) Preguntas basadas en DATA (empleo y eventos):
- Si la pregunta se refiere al mercado laboral, empleabilidad, salarios, sectores con más demanda, tipos de puestos, ciudades con más ofertas, eventos de empleo, etc., revisa el contenido de DATA y úsalo para dar una respuesta fundamentada.
- Menciona ejemplos concretos de ofertas o eventos solo si aparecen en DATA.
- Si falta información importante en DATA, dilo claramente.

3) Modo JSON estructurado (solo si el usuario lo pide):
- Si el usuario pide explícitamente un "análisis en JSON", "formato JSON" o algo similar, prepara un ÚNICO objeto JSON con exactamente estas claves de nivel superior:
  - "fecha_analisis" (string, formato YYYY-MM-DD)
  - "resumen_mercado" (string corto, 3–5 líneas máximo)
  - "sectores_con_mayor_demanda" (lista de objetos)
  - "habilidades_mas_pedidas" (lista de strings)
  - "eventos_relevantes" (lista de objetos)
  - "recomendaciones" (lista de strings)

  Donde:
  - En "sectores_con_mayor_demanda", cada objeto tiene:
      - "sector"
      - "cantidad_ofertas_aproximada"
      - "ejemplos_puestos"
  - En "eventos_relevantes", cada objeto tiene:
      - "titulo"
      - "ciudad"
      - "fecha_inicio"
      - "url"

  Reglas específicas para el modo JSON:
  - Devuelve SOLO el JSON, sin texto adicional antes ni después.
  - No uses bloques de código ni escribas ```json ni ``` de ningún tipo.
  - Usa únicamente la información que aparece en DATA. Si algo importante no se puede saber a partir de DATA, menciónalo en "recomendaciones".

4) Formato por defecto:
- Si el usuario NO pide JSON explícitamente, NO respondas en JSON: responde en texto normal, como un asistente conversacional.
""".strip()


def _init_gemini_model() -> GenerativeModel:
    """
    Inicializa Vertex AI usando las credenciales definidas en config:

    - Si existe config.GCP_SERVICE_ACCOUNT_JSON (modo deploy / Streamlit Cloud),
      lo usa directamente sin necesidad de archivo físico.
    - Si no, intenta usar config.GCP_SERVICE_ACCOUNT_FILE (modo local).
    - Si tampoco hay, intenta inicializar sin credenciales explícitas
      (por ejemplo si ya tienes auth por gcloud).
    """
    credentials = None

    # 1) Caso deploy: JSON completo en una variable (st.secrets → config.GCP_SERVICE_ACCOUNT_JSON)
    if config.GCP_SERVICE_ACCOUNT_JSON:
        try:
            info = json.loads(config.GCP_SERVICE_ACCOUNT_JSON)
            credentials = service_account.Credentials.from_service_account_info(info)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                "GCP_SERVICE_ACCOUNT_JSON no es un JSON válido. "
                "Revisa el valor que pusiste en los secrets."
            ) from e

    # 2) Caso local: ruta a un archivo JSON en tu máquina
    elif config.GCP_SERVICE_ACCOUNT_FILE:
        if not os.path.exists(config.GCP_SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(
                f"No se encontró el archivo de credenciales en: {config.GCP_SERVICE_ACCOUNT_FILE}"
            )
        credentials = service_account.Credentials.from_service_account_file(
            config.GCP_SERVICE_ACCOUNT_FILE
        )

    # 3) Inicializar Vertex AI
    if credentials:
        vertexai.init(
            project=config.GCP_PROJECT_ID,
            location=config.GCP_LOCATION,
            credentials=credentials,
        )
    else:
        # Fallback: intentar sin credenciales explícitas (por si usas ADC)
        vertexai.init(
            project=config.GCP_PROJECT_ID,
            location=config.GCP_LOCATION,
        )

    return GenerativeModel(config.GEMINI_MODEL_NAME)


def build_data_context():
    """
    Lee jobs y events desde Redis y construye el string DATA.
    """
    client = get_redis_client()

    jobs = load_data_from_redis("scraper_4", client=client)
    events = load_data_from_redis("events_peru", client=client)

    contexto = {
        "jobs": jobs,
        "events": events,
    }

    data_str = json.dumps(contexto, ensure_ascii=False)

    if len(data_str) > MAX_DATA_CHARS:
        data_str = data_str[:MAX_DATA_CHARS]

    return data_str, jobs, events


def _build_history_block(history: Optional[List[Dict[str, str]]]) -> str:
    """
    Convierte el historial en un bloque de texto tipo:

    Historial reciente:
    Usuario: ...
    Asistente: ...
    """
    if not history:
        return ""

    lines = ["Historial reciente (últimos turnos):"]
    # Nos quedamos con los últimos 8 intercambios para no inflar demasiado el prompt
    for turn in history[-16:]:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if not content:
            continue
        if role == "assistant":
            prefix = "Asistente:"
        else:
            prefix = "Usuario:"
        lines.append(f"{prefix} {content}")

    return "\n".join(lines) + "\n\n"


def generate_insights(
    user_question: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
):
    """
    Llama a Gemini usando los datos de Redis y devuelve:
      - un dict (JSON parseado) si la respuesta es JSON válido
      - o un string (texto crudo) si no se pudo parsear.

    history: lista opcional de mensajes anteriores, cada uno con:
      {"role": "user" | "assistant", "content": "texto..."}
    """
    data_str, jobs, events = build_data_context()

    if not jobs and not events:
        raise RuntimeError(
            "No hay datos en Redis. "
            "Primero ejecuta scraper.py y ticket_master.py para poblar jobs y eventos."
        )

    model = _init_gemini_model()

    fecha_analisis = datetime.now().strftime("%Y-%m-%d")

    history_block = _build_history_block(history)

    prompt = (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"Hoy es {fecha_analisis}.\n\n"
        f"DATA (resumen de ofertas y eventos):\n"
        f"{data_str}\n\n"
        f"{USER_TASK}\n\n"
        f"{history_block}"
    )

    if user_question:
        prompt += f"Pregunta actual del usuario: {user_question}\n"

    response = model.generate_content(
        prompt,
        generation_config=GenerationConfig(
            temperature=0.5,          # un poquito más creativo para razonar
            max_output_tokens=3072,   # más tokens para respuestas completas
            top_p=0.95,
            top_k=40,
        ),
    )

    text = (response.text or "").strip()

    # Por si el modelo mete accidentalmente ```json ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Intentamos parsear JSON SOLO si de verdad parece JSON
    if text.startswith("{") or text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Si falla, devolvemos el texto tal cual
            return text
    else:
        return text


if __name__ == "__main__":
    # Prueba rápida desde terminal
    result = generate_insights("¿Qué habilidades blandas se repiten más en las ofertas recientes?")
    if isinstance(result, dict):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)
