"""
Configuración centralizada del modelo con dataclass y valores por defecto.

Incluye:
- Parámetros físicos/astronómicos
- Parámetros sociológicos y tecnológicos
- Benchmarks de validación tipo Drake
- Flags de optimización (cores, caps)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
import json

@dataclass
class Parametros:
    # ---- Escala galáctica / astronomía ----
    num_estrellas: float = 2e11
    fraccion_con_planetas: float = 1.0
    planetas_zona_habitable_promedio: float = 0.22
    radio_galaxia: float = 50000.0
    espesor_disco: float = 1000.0
    edad_galaxia: float = 13.6e9
    ghz_inner_radius: float = 10000.0   # ly — límite interior para análisis (Lineweaver 2004)
    ghz_outer_radius: float = 30000.0   # ly — límite exterior para análisis (Lineweaver 2004)
    probabilidad_ghz: float = 0.8       # obsoleto: reemplazado por perfil continuo Lineweaver
    ghz_peak_radius: float = 25000.0    # ly — pico de habitabilidad (Lineweaver 2004, Science 303)
    ghz_sigma: float = 8000.0           # ly — ancho del perfil gaussiano de habitabilidad
    escala_radio_bulbo: float = 3000.0
    escala_altura_disco: float = 300.0

    # ---- Filtros (Drake) ----
    filtro_pesimista: Dict[str, float] = field(default_factory=lambda: {"f_l": 1e-3, "f_i": 1e-3, "f_c": 1e-2})
    filtro_optimista: Dict[str, float] = field(default_factory=lambda: {"f_l": 1e-1, "f_i": 1e-2, "f_c": 2e-1})

    # ---- Duraciones de civilización ----
    vida_media_civilizacion: float = 1e4
    vida_media_extendida: float = 1.43e8
    distribucion_L: Dict[str, float] = field(default_factory=lambda: {"tipo": "lognormal", "media": 10000.0, "sigma": 1.5, "min": 100.0, "max": 1e6})

    # ---- Tecnología de detección ----
    tecnologia_deteccion: Dict[str, float] = field(default_factory=lambda: {
        "radio_max_realista": 1000.0, "eficiencia_evolucion": 1e-3,
        "d0_atenuacion": 100.0,
        "probabilidad_falsos_positivos": 0.01, "probabilidad_falsos_negativos": 0.05
    })

    # ---- Sociología ----
    sociologia: Dict[str, float] = field(default_factory=lambda: {
        "probabilidad_ataque_agresivo": 0.3, "probabilidad_ataque_defensivo": 0.4,
        "probabilidad_pacifico": 0.2, "probabilidad_curioso": 0.1, "umbral_amenaza": 0.7
    })

    # ---- Motor / optimización ----
    propagacion: Dict[str, float] = field(default_factory=lambda: {"velocidad_luz": 1.0})
    optimizacion: Dict[str, int] = field(default_factory=lambda: {"num_cores": os.cpu_count() or 1, "target_fps": 15})
    sensibilidad: Dict[str, int] = field(default_factory=lambda: {"N": 512})

    # ---- Benchmarks de validación ----
    # Calibración cualitativa (no validación): compara N_c simulado con Drake clásico.
    # tolerance=0.5 → dentro de rango si el error relativo es ≤ 50%.
    # Con parámetros pesimistas N_c es ordenes de magnitud menor que Drake,
    # lo que es esperado y documenta la diferencia entre escenarios.
    benchmarks: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "drake_1961": {"N": 1e11, "fp": 0.4, "ne": 2, "fl": 1.0, "fi": 0.01, "fc": 0.01, "L": 10000.0, "tolerance": 0.5},
        "drake_modern": {"N": 2e11, "fp": 1.0, "ne": 0.22, "fl": 0.13, "fi": 0.01, "fc": 0.01, "L": 1000.0, "tolerance": 0.5}
    })

    # ---- Caps prácticos (para escenarios gigantes) ----
    optimistic_cap: int = int(os.getenv("OPTIMISTIC_CAP", "300000"))

    def to_json(self) -> str:
        """Devuelve un snapshot JSON ordenado de la configuración para hashing/registro."""
        return json.dumps(self.__dict__, sort_keys=True, default=str, ensure_ascii=False)
