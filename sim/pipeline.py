"""
Orquestación de la simulación completa:
- Paso 1 y 2 (N_hp y N_c para escenarios)
- Simulación de catálogos
- Coexistencia temporal
- Paso 5 (dinámica Bosque Oscuro)
- Validaciones y sensibilidad
- Visualización estática simple (mapa)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, Tuple, Optional

from ..common.config import Parametros
from ..common.io_utils import Logger, ensure_structure, save_txt, save_csv, save_json
from .espacio import generar_posiciones
from .tiempos import generar_duraciones, analizar_coexistencia
from .dinamica import paso5_bosque_oscuro
from .sociologia import normalizar_probabilidades
from .validacion import checks_integridad, calibracion_drake
from .sensibilidad import sobol_drake, sobol_bosque_oscuro

def _simular_universo(n_civs: int, p: Parametros, logger: Logger, escenario: str) -> pd.DataFrame:
    logger.log(f"FASE 3: Simulando universo ({escenario}, {n_civs:,} civs)...")
    from .factory import crear_catalogo
    return crear_catalogo(n_civs, p)

def _visualizar_mapa(df: pd.DataFrame, rutas: Dict[str, str], p: Parametros, nombre: str, dpi: int) -> str:
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor("black"); fig.set_facecolor("black")
    r = p.radio_galaxia
    ax.scatter(df["posicion_x_ly"], df["posicion_y_ly"], s=8, alpha=0.6, edgecolors="cyan", facecolors="none", linewidths=0.3)
    des = df[df["estado"] == "destruida"]
    if not des.empty:
        ax.scatter(des["posicion_x_ly"], des["posicion_y_ly"], s=10, color="red", alpha=0.8, label="Destruidas")
        ax.legend(loc="upper right", facecolor="black", edgecolor="white")

    ax.add_artist(plt.Circle((0, 0), r, color="cyan", fill=False, ls="--", lw=0.6))
    ax.set_xlim(-r * 1.1, r * 1.1); ax.set_ylim(-r * 1.1, r * 1.1)
    ax.set_aspect("equal"); ax.set_title(f"Mapa Galáctico ({nombre})", color="white")
    out = os.path.join(rutas["visualizaciones"], f"mapa_estatico_{nombre}.png")
    fig.savefig(out, dpi=dpi, facecolor="black", bbox_inches="tight")
    plt.close(fig)
    return out

def run_full_pipeline(outdir: str, seed: Optional[int], full_optimistic: bool, enable_ftl: bool,
                      dpi: int, do_sensitivity: bool, generate_report: bool) -> Dict[str, Any]:
    np.random.seed(seed if seed is not None else None)
    rutas = ensure_structure(outdir)
    logger = Logger(os.path.join(rutas["logs"], "simulation_log.txt"))
    logger.log("Sistema de simulación inicializado.")
    p = Parametros()
    normalizar_probabilidades(p)

    # Paso 1 y 2
    logger.log("FASE 1: Calculando línea base galáctica...")
    N_hp = p.num_estrellas * p.fraccion_con_planetas * p.planetas_zona_habitable_promedio
    save_txt(os.path.join(rutas["analisis"], "paso1_linea_base_galactica.txt"),
             f"PLANETAS POTENCIALMENTE HABITABLES (N_hp): {N_hp:,.0f}")

    logger.log("FASE 2: Aplicando filtros Drake...")
    N_c_pes = int(N_hp * p.filtro_pesimista["f_l"] * p.filtro_pesimista["f_i"] * p.filtro_pesimista["f_c"])
    N_c_opt = int(N_hp * p.filtro_optimista["f_l"] * p.filtro_optimista["f_i"] * p.filtro_optimista["f_c"])
    save_txt(os.path.join(rutas["analisis"], "paso2_filtro_pesimista.txt"),
             f"NÚMERO DE CIVILIZACIONES (N_c Pesimista): {N_c_pes:,}")
    save_txt(os.path.join(rutas["analisis"], "paso2.1_filtro_optimista.txt"),
             f"NÚMERO DE CIVILIZACIONES (N_c Optimista): {N_c_opt:,}")

    # Simulaciones
    cat_pes = _simular_universo(N_c_pes, p, logger, "pesimista")
    save_csv(os.path.join(rutas["catalogos"], "catalogo_civilizaciones_pesimista.csv"), cat_pes)

    cat_opt = None
    if full_optimistic:
        n_opt = min(N_c_opt, p.optimistic_cap)
        logger.log(f"FASE 3: Simulando universo (optimista, CAP={n_opt:,} civs)...")
        cat_opt = _simular_universo(n_opt, p, logger, "optimista")
        save_csv(os.path.join(rutas["catalogos"], "catalogo_civilizaciones_optimista.csv"), cat_opt)

    # Coexistencia temporal + mapas
    from .tiempos import analizar_coexistencia
    max_pes, act_pes = analizar_coexistencia(cat_pes, p)
    mapa_pes = _visualizar_mapa(cat_pes, rutas, p, "pesimista", dpi)

    max_opt = act_opt = mapa_opt = None
    if cat_opt is not None:
        max_opt, act_opt = analizar_coexistencia(cat_opt, p)
        mapa_opt = _visualizar_mapa(cat_opt, rutas, p, "optimista", dpi)

    # Paso 5 (dinámica)
    logger.log(f"FASE 5: Dinámica Bosque Oscuro (pesimista), FTL={'ON' if enable_ftl else 'OFF'}...")
    fin_pes, hist_pes = paso5_bosque_oscuro(cat_pes, p, ftl_enabled=enable_ftl)
    save_csv(os.path.join(rutas["catalogos"], "catalogo_final_paso5_pesimista.csv"), fin_pes)
    save_csv(os.path.join(rutas["catalogos"], "historial_destruccion_paso5_pesimista.csv"), hist_pes)

    fin_opt = hist_opt = None
    if cat_opt is not None:
        logger.log(f"FASE 5: Dinámica Bosque Oscuro (optimista), FTL={'ON' if enable_ftl else 'OFF'}...")
        fin_opt, hist_opt = paso5_bosque_oscuro(cat_opt, p, ftl_enabled=enable_ftl)
        save_csv(os.path.join(rutas["catalogos"], "catalogo_final_paso5_optimista.csv"), fin_opt)
        save_csv(os.path.join(rutas["catalogos"], "historial_destruccion_paso5_optimista.csv"), hist_opt)

    # Integridad y validación externa
    ch_pes = checks_integridad(fin_pes)
    save_json(os.path.join(rutas["validacion"], "integridad_pesimista.json"), ch_pes)
    val_pes = calibracion_drake(N_c_pes, p)
    save_json(os.path.join(rutas["validacion"], "calibracion_drake_pesimista.json"), val_pes)

    if fin_opt is not None:
        ch_opt = checks_integridad(fin_opt)
        save_json(os.path.join(rutas["validacion"], "integridad_optimista.json"), ch_opt)
        val_opt = calibracion_drake(N_c_opt, p)
        save_json(os.path.join(rutas["validacion"], "calibracion_drake_optimista.json"), val_opt)

    # Sensibilidad (opcional)
    sob = None
    sob_bf = None
    if do_sensitivity:
        sob = sobol_drake(p)
        if sob is not None:
            save_json(os.path.join(rutas["sensibilidad"], "sobol_drake.json"),
                      {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in sob.items()})
        logger.log("SENSIBILIDAD: Sobol dinámica Bosque Oscuro (mini-sim 100 civs × N muestras)...")
        sob_bf = sobol_bosque_oscuro(p)
        if sob_bf is not None:
            save_json(os.path.join(rutas["sensibilidad"], "sobol_bosque_oscuro.json"), sob_bf)

    # Reporte (ligero, sin dependencias pesadas)
    if generate_report:
        resumen = {
            "N_hp": N_hp, "N_c_pesimista": N_c_pes, "max_coex_pesimista": max_pes, "activas_pesimista": act_pes,
            "destrucciones_p5_pesimista": int(len(hist_pes)),
            "mapa_pesimista_path": mapa_pes
        }
        if cat_opt is not None:
            resumen.update({
                "N_c_optimista": N_c_opt, "max_coex_optimista": max_opt, "activas_optimista": act_opt,
                "destrucciones_p5_optimista": int(len(hist_opt) if hist_opt is not None else 0),
                "mapa_optimista_path": mapa_opt
            })
        save_json(os.path.join(rutas["reportes"], "resumen_simulacion.json"), resumen)

    # Resultado final para la CLI
    result = {
        "paths": rutas,
        "N_hp": N_hp,
        "pesimista": {"N_c": N_c_pes, "max_coex": max_pes, "activas_hoy": act_pes, "historial_len": int(len(hist_pes))},
    }
    if cat_opt is not None:
        result["optimista"] = {"N_c": N_c_opt, "max_coex": max_opt, "activas_hoy": act_opt, "historial_len": int(len(hist_opt))}
    if sob is not None:
        result["sensibilidad"] = True
    return result
