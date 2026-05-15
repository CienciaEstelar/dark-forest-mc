# bosque_oscuro/analysis/narrativa_llm.py
# -*- coding: utf-8 -*-
"""
MÓDULO: narrativa_llm
=====================

Genera una narrativa técnica (Markdown) a partir de las métricas producidas
por el análisis del proyecto “Bosque Oscuro”.

NOVEDAD EN ESTA VERSIÓN
-----------------------
- Se fija explícitamente la unidad de distancia en **años luz (ly)**,
  porque la simulación usa coordenadas *_ly.
- Se formatean las distancias del JSON antes de mandarlas al LLM.
- Se añade un bloque # UNIDADES en el prompt para que la LLM NO diga “unidades”.

Requisitos:
- GEMINI_API_KEY_PRO o GEMINI_API_KEY en el entorno
- `google-genai` instalado
- opcional: `python-dotenv`
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional

# -----------------------------------------------------------
# 1. Cargar .env si existe
# -----------------------------------------------------------
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


# -----------------------------------------------------------
# 2. Helpers de datos
# -----------------------------------------------------------
def get_or_nd(data_dict: Dict[str, Any], key: str, default: str = "N/D") -> str:
    """Helper seguro para extraer datos con fallback claro."""
    try:
        value = data_dict.get(key, default)
        return value if value not in [None, ""] else default
    except Exception:
        return default


def format_distance_ly(value: Any) -> str:
    """
    Intenta devolver la distancia con unidad 'ly'.
    Casos:
    - número (int/float) → "1234 ly"
    - string que ya trae 'ly' → se deja igual
    - string cualquiera → se deja igual
    - None → "N/D"
    """
    if value is None:
        return "N/D"
    # ya viene con unidad
    if isinstance(value, str) and ("ly" in value.lower() or "luz" in value.lower()):
        return value
    # numérico
    if isinstance(value, (int, float)):
        # sin coma, esto lo puedes tunear a "{value:,.0f} ly"
        return f"{value} ly"
    # string raro → lo dejamos
    return str(value)


# -----------------------------------------------------------
# 3. Prompt híbrido con UNIDADES
# -----------------------------------------------------------
def build_bosque_prompt(metrics: Dict[str, Any]) -> str:
    """
    Construye el prompt analítico para narrativa técnica del Bosque Oscuro.
    Aquí ya forzamos que las distancias sean en años luz (ly).
    """
    vecino = metrics.get("vecino", {})
    ghz = metrics.get("ghz", {})
    destr = metrics.get("destrucciones", {})

    # === datos ===
    distancia_media_raw = get_or_nd(vecino, "media")
    distancia_mediana_raw = get_or_nd(vecino, "mediana")

    # los pasamos por el formateador de ly
    distancia_media = format_distance_ly(distancia_media_raw)
    distancia_mediana = format_distance_ly(distancia_mediana_raw)

    porcentaje_ghz = get_or_nd(ghz, "porcentaje_en_ghz")
    civs_destruidas = get_or_nd(destr, "destruidas")
    total_civs = get_or_nd(destr, "total_civs")
    tasa_destruccion = get_or_nd(destr, "tasa_destruccion_pct")

    prompt = f"""
# PERSONA
Eres un astrofísico computacional especializado en SETI, dinámica de civilizaciones galácticas
y simulaciones tipo “Bosque Oscuro”. Tu prioridad es la **honestidad de los datos** y la
**explicabilidad** del modelo.

# UNIDADES
- Todas las distancias espaciales están expresadas en **años luz (ly)** porque el modelo
  de simulación trabaja en coordenadas `*_ly`.
- Si algún valor no indica unidad, debes decir explícitamente: “(en años luz, ly)”.
- Las proporciones están en **%**.

# TAREA
Redacta un **informe técnico-científico** (600-900 palabras) que explique los resultados
de una simulación del Bosque Oscuro. La audiencia son investigadores de astroinformática.

# DATOS DE SIMULACIÓN (USA SOLO ESTOS)
- Aislamiento interestelar (distancia al vecino más cercano):
  - media: {distancia_media}
  - mediana: {distancia_mediana}
- Distribución galáctica:
  - {porcentaje_ghz}% de las civilizaciones se ubican en la Zona Galáctica Habitable (GHZ).
- Dinámica de destrucción:
  - civilizaciones destruidas: {civs_destruidas}
  - total de civilizaciones simuladas: {total_civs}
  - tasa de destrucción: {tasa_destruccion} %

# REGLAS ESTRICTAS
1. **Fidelidad de datos**: No inventes números ni porcentajes que no estén arriba.
2. Si un dato NO está disponible, escribe: "[Análisis limitado: dato no disponible]".
3. No digas que viste más gráficos o tablas si no existen en los datos.
4. Enmarca la simulación dentro de la Paradoja de Fermi y la hipótesis del Bosque Oscuro,
   pero SIN convertirlo en un ensayo de ciencia ficción.
5. Escribe en español técnico, pero legible.
6. Menciona la unidad **años luz (ly)** al menos una vez en la sección de aislamiento.

# ESTRUCTURA REQUERIDA (usa estos títulos exactos)
## CONTEXTO Y PARÁMETROS
## ANÁLISIS DE AISLAMIENTO CÓSMICO
## DINÁMICA BOSQUE OSCURO
## FACTORES GEOGALÁCTICOS
## ESCENARIOS DE SENSIBILIDAD
## IMPLICACIONES Y LÍNEAS FUTURAS

# FORMATO
- Usa Markdown.
- No coloques código.
- No uses listas demasiado largas, mezcla párrafos con viñetas cuando ayude a la claridad.
""".strip()

    if os.getenv("DEBUG_LLM_PROMPT"):
        print("=== DEBUG PROMPT BOSQUE OSCURO ===")
        print(prompt)
        print("=================================")

    return prompt


# -----------------------------------------------------------
# 4. Validación de salida
# -----------------------------------------------------------
def validate_llm_output(
    text: str,
    expected_sections: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if expected_sections is None:
        expected_sections = [
            "CONTEXTO Y PARÁMETROS",
            "ANÁLISIS DE AISLAMIENTO CÓSMICO",
            "DINÁMICA BOSQUE OSCURO",
            "FACTORES GEOGALÁCTICOS",
            "ESCENARIOS DE SENSIBILIDAD",
            "IMPLICACIONES Y LÍNEAS FUTURAS",
        ]

    text_lower = text.lower()
    result = {
        "all_present": True,
        "missing_sections": [],
        "word_count": len(text.split()),
        "section_details": {},
    }

    for section in expected_sections:
        ok = section.lower() in text_lower
        result["section_details"][section] = ok
        if not ok:
            result["all_present"] = False
            result["missing_sections"].append(section)

    # chequeo rápido de unidad
    if "ly" not in text_lower and "luz" not in text_lower:
        result["all_present"] = False
        result["missing_sections"].append("mención explícita de unidad (ly)")

    return result


# -----------------------------------------------------------
# 5. Proveedores
# -----------------------------------------------------------
def _get_gemini_api_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY_PRO") or os.getenv("GEMINI_API_KEY")


def _call_gemini(prompt: str, model: str) -> str:
    api_key = _get_gemini_api_key()
    if not api_key:
        raise RuntimeError("No se encontró GEMINI_API_KEY_PRO ni GEMINI_API_KEY en el entorno.")

    from google import genai  # type: ignore

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    if hasattr(resp, "output_text") and resp.output_text:
        return resp.output_text
    if hasattr(resp, "text") and resp.text:
        return resp.text
    return str(resp)


def _call_openai(prompt: str, model: str) -> str:
    from openai import OpenAI  # type: ignore

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No se encontró OPENAI_API_KEY en el entorno.")

    client = OpenAI(api_key=api_key)
    chat = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return chat.choices[0].message.content


# -----------------------------------------------------------
# 6. API pública para run_pipeline
# -----------------------------------------------------------
def generate_narrative(
    metrics: Dict[str, Any],
    provider: str = "gemini",
    model: str = "gemini-2.5-pro",
    outfile: Optional[str] = None,
    sim_dir: Optional[str] = None,
    analysis_dir: Optional[str] = None,
    pdf_path: Optional[str] = None,
) -> str:
    prompt = build_bosque_prompt(metrics or {})

    if provider == "none":
        narrative = prompt
    elif provider == "gemini":
        narrative = _call_gemini(prompt, model)
    elif provider == "openai":
        narrative = _call_openai(prompt, model)
    else:
        raise ValueError(f"Proveedor LLM no soportado: {provider}")

    diag = validate_llm_output(narrative)
    if not diag["all_present"]:
        print(f"⚠️ Narrativa LLM: faltan secciones o unidad: {diag['missing_sections']}")

    # decidir salida
    if not outfile:
        if analysis_dir:
            os.makedirs(analysis_dir, exist_ok=True)
            outfile = os.path.join(analysis_dir, "informe_narrativo_llm.md")
        else:
            outfile = "informe_narrativo_llm.md"

    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(narrative)

    print(f"✅ Narrativa LLM generada en: {outfile}")
    return outfile
