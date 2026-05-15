"""
Validación de robustez / sensibilidad a la semilla.

Dado una lista de carpetas de simulaciones, calcula:
- distancia media al vecino
- % en GHZ
- nº de civs
y luego saca medias, std y coeficiente de variación.
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

def analizar_robustez(directorios: List[str | Path]) -> Dict[str, Any]:
    resultados = []
    for d in directorios:
        d = Path(d)
        cat_path = d / "catalogos" / "catalogo_civilizaciones_pesimista.csv"
        if not cat_path.exists():
            continue
        df = pd.read_csv(cat_path)
        if len(df) < 2:
            continue

        pts = df[["posicion_x_ly", "posicion_y_ly", "posicion_z_ly"]].to_numpy()
        kdt = KDTree(pts)
        distancias, _ = kdt.query(pts, k=2)
        dvc = distancias[:, 1]

        df["distancia_centro_2d"] = np.sqrt(df["posicion_x_ly"] ** 2 + df["posicion_y_ly"] ** 2)
        ghz_mask = (df["distancia_centro_2d"] >= 10000) & (df["distancia_centro_2d"] <= 30000)
        pct_ghz = float(len(df[ghz_mask]) / len(df) * 100.0)

        resultados.append({
            "simulacion": d.name,
            "media_vecino": float(dvc.mean()),
            "pct_ghz": pct_ghz,
            "n_civs": int(len(df))
        })

    if not resultados:
        return {}

    df_res = pd.DataFrame(resultados)
    stats = {
        "n_simulaciones": int(len(df_res)),
        "media_vecino_global": float(df_res["media_vecino"].mean()),
        "std_vecino_global": float(df_res["media_vecino"].std()),
        "cv_vecino_global": float(df_res["media_vecino"].std() / df_res["media_vecino"].mean() * 100.0),
        "media_pct_ghz_global": float(df_res["pct_ghz"].mean()),
        "std_pct_ghz_global": float(df_res["pct_ghz"].std()),
        "cv_pct_ghz_global": float(df_res["pct_ghz"].std() / df_res["pct_ghz"].mean() * 100.0),
        "media_civs": float(df_res["n_civs"].mean()),
        "detallado": resultados,
    }
    return stats
