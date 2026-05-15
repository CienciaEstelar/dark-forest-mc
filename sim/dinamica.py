"""
Dinámica del Bosque Oscuro (Paso 5) optimizada:

- Procesamiento por tiempos de nacimiento (event-driven básico)
- Índice espacial con cKDTree sobre activas en cada evento
- Consulta por radio (query_ball_point) → reduce drásticamente pares evaluados
- Arrays numpy extraídos una vez al inicio; cero operaciones pandas dentro del loop

Nota: Aquí preferimos claridad y robustez al micro-optimizar. Es un gran salto frente a O(N^2).
"""

import math
import numpy as np
import pandas as pd
from typing import Tuple
from scipy.spatial import cKDTree
from ..common.config import Parametros
from .tecnologia import prob_deteccion, prob_deteccion_batch
from .sociologia import (decision_ataque, decision_presa,
                         RADIO_VECINDAD_PRESA, MODIF_DETECCION_PRESA,
                         MODIF_DETECCION_CAZADOR)

def paso5_bosque_oscuro(catalogo_inicial: pd.DataFrame, p: Parametros, ftl_enabled: bool = False, disable_attacks: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ejecuta la dinámica del Bosque Oscuro:
    - En cada tiempo de nacimiento, toma las civs activas
    - Construye un índice espacial y para cada 'cazador' consulta presas en su radio de detección
    - Evalúa prob. detección + decisión de ataque → marca destruidas (cambia estado/tiempo_muerte)
    """
    if catalogo_inicial.empty:
        return catalogo_inicial, pd.DataFrame(columns=["tiempo_evento_yr","cazador_id","presa_id","distancia_ly"])

    catalogo = catalogo_inicial.copy()
    catalogo["tiempo_muerte_yr"] = catalogo["tiempo_nacimiento_yr"] + float(p.vida_media_extendida)
    catalogo["estrategia_actual"] = "NINGUNA"

    v_luz = float(p.propagacion["velocidad_luz"])
    ftl = 10.0 if ftl_enabled else 1.0
    RADIO_ZONA_PELIGROSA = 2000.0   # ly

    # Extraer todos los arrays numpy una vez — elimina overhead pandas dentro del loop
    _ids_all    = catalogo["id_civilizacion"].to_numpy()
    _estado     = catalogo["estado"].to_numpy().copy()            # mutable
    _t_nac_all  = catalogo["tiempo_nacimiento_yr"].to_numpy()
    _t_muerte   = catalogo["tiempo_muerte_yr"].to_numpy().copy()  # mutable
    _pos_all    = catalogo[["posicion_x_ly", "posicion_y_ly", "posicion_z_ly"]].to_numpy(dtype=np.float32)
    _niveles    = catalogo["nivel_tecnologico_inicial"].to_numpy()
    _tipos      = catalogo["tipo_sociologico"].to_numpy()
    _estrategia = np.full(len(catalogo), "NINGUNA", dtype=object)

    # Lookup civ_id → índice global en O(1)
    _id_to_gidx = {int(cid): i for i, cid in enumerate(_ids_all)}

    eventos_t = np.sort(np.unique(_t_nac_all))

    historial = []
    all_destruidas_pos: list = []
    _tree_des = None
    _n_des_cached = 0

    for t in eventos_t:
        # Filtro en numpy puro: sin pandas
        mask = (_estado == "activa") & (_t_nac_all <= t) & (_t_muerte > t)
        idx_activas = np.where(mask)[0]

        if len(idx_activas) < 2:
            continue

        pts     = _pos_all[idx_activas]          # float32, copia por fancy-index
        tree    = cKDTree(pts)
        ids     = _ids_all[idx_activas]
        niveles = _niveles[idx_activas]
        nac     = _t_nac_all[idx_activas]
        tipos   = _tipos[idx_activas]

        # --- Estrategia de cada civ activa (Mejoras 1 y 3) ---
        estrategias_t: dict = {}
        if all_destruidas_pos:
            if len(all_destruidas_pos) != _n_des_cached:
                des_arr = np.array(all_destruidas_pos, dtype=np.float32)
                _tree_des = cKDTree(des_arr)
                _n_des_cached = len(all_destruidas_pos)
            counts_vec = _tree_des.query_ball_point(pts, r=RADIO_VECINDAD_PRESA, return_sorted=False)
            counts_zp  = _tree_des.query_ball_point(pts, r=RADIO_ZONA_PELIGROSA,  return_sorted=False)
            for idx_s, civ_id_s in enumerate(ids):
                strat = decision_presa(str(tipos[idx_s]), len(counts_vec[idx_s]), len(counts_zp[idx_s]))
                estrategias_t[int(civ_id_s)] = strat
                _estrategia[idx_activas[idx_s]] = strat
        else:
            for idx_s, civ_id_s in enumerate(ids):
                strat = decision_presa(str(tipos[idx_s]), 0, 0)
                estrategias_t[int(civ_id_s)] = strat
                _estrategia[idx_activas[idx_s]] = strat

        destruidas_ids = set()
        # Mapa local civ_id → índice en pts (para acumular posición de destruidas)
        _local_map = {int(ids[i]): i for i in range(len(ids))}

        for idx_caz, civ_id in enumerate(ids):
            edad = float(t - nac[idx_caz])
            radio_info = edad * v_luz * ftl
            if radio_info <= 0.0:
                continue

            vecinos = tree.query_ball_point(pts[idx_caz], r=radio_info)
            if not vecinos:
                continue

            # ── Filtrar presas válidas y recolectar modificadores ──
            caz_id_int = int(civ_id)
            _mod_caz = MODIF_DETECCION_CAZADOR.get(
                estrategias_t.get(caz_id_int, "NINGUNA"), 1.0)

            vecinos_validos = []
            mods_presa = []
            for j in vecinos:
                if j == idx_caz:
                    continue
                if ids[j] in destruidas_ids:
                    continue
                vecinos_validos.append(j)
                mods_presa.append(MODIF_DETECCION_PRESA.get(
                    estrategias_t.get(int(ids[j]), "NINGUNA"), 1.0))

            if not vecinos_validos:
                continue

            nv = len(vecinos_validos)
            vecinos_arr = np.array(vecinos_validos, dtype=np.int64)
            mods_arr = np.array(mods_presa, dtype=np.float64)

            # ── Vectorizado: distancias 3D ──
            dxyz = pts[idx_caz] - pts[vecinos_arr]
            dists = np.sqrt(np.sum(dxyz * dxyz, axis=1))

            # ── Vectorizado: prob_deteccion batch ──
            pr_det = prob_deteccion_batch(dists, edad, float(niveles[idx_caz]), p)
            pr_det *= mods_arr
            pr_det *= _mod_caz
            np.clip(pr_det, 0.0, 1.0, out=pr_det)

            # ── Vectorizado: Bernoulli para todas las presas ──
            randoms = np.random.random(nv)
            detecciones = randoms < pr_det

            # ── Procesar solo detecciones positivas ──
            for i in range(nv):
                if not detecciones[i]:
                    continue
                j = vecinos_validos[i]
                presa_id = ids[j]
                dist = float(dists[i])

                caz_row = {
                    "tipo_sociologico": tipos[idx_caz],
                    "nivel_tecnologico_inicial": niveles[idx_caz]
                }
                presa_row = {
                    "tipo_sociologico": tipos[j],
                    "nivel_tecnologico_inicial": niveles[j]
                }
                if not disable_attacks and decision_ataque(caz_row, presa_row, p):
                    destruidas_ids.add(presa_id)
                    historial.append({
                        "tiempo_evento_yr": t,
                        "cazador_id": caz_id_int,
                        "presa_id": int(presa_id),
                        "distancia_ly": dist
                    })

        if destruidas_ids:
            for des_id in destruidas_ids:
                g_idx = _id_to_gidx[int(des_id)]
                _estado[g_idx]   = "destruida"
                _t_muerte[g_idx] = t
                l_idx = _local_map[int(des_id)]
                all_destruidas_pos.append(pts[l_idx].tolist())

    # Escribir estado final de vuelta al DataFrame
    catalogo["estado"]           = _estado
    catalogo["tiempo_muerte_yr"] = _t_muerte
    catalogo["estrategia_actual"] = _estrategia

    hist_df = pd.DataFrame(historial, columns=["tiempo_evento_yr","cazador_id","presa_id","distancia_ly"])
    return catalogo, hist_df
