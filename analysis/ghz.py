"""
Análisis de la Zona Galáctica Habitable (GHZ).
"""

from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from ..common.io_utils import save_txt
from ..common.config import Parametros

def analizar_ghz(df: pd.DataFrame, p: Parametros, out_dir: str | Path, dpi: int = 600) -> Tuple[Path, Dict]:
    """
    Calcula qué porcentaje de civilizaciones cae dentro de la GHZ y compara duración.

    Devuelve:
    - ruta del PNG
    - dict con métricas clave
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if "distancia_centro_2d" not in df.columns:
        df = df.copy()
        df["distancia_centro_2d"] = np.sqrt(df["posicion_x_ly"] ** 2 + df["posicion_y_ly"] ** 2)

    mask_ghz = (df["distancia_centro_2d"] >= p.ghz_inner_radius) & (df["distancia_centro_2d"] <= p.ghz_outer_radius)
    civs_in = df[mask_ghz]
    civs_out = df[~mask_ghz]

    stats = {
        "total": int(len(df)),
        "civs_en_ghz": int(len(civs_in)),
        "civs_fuera_ghz": int(len(civs_out)),
        "porcentaje_en_ghz": float(len(civs_in) / len(df) * 100.0) if len(df) else 0.0,
        "duracion_media_ghz": float(civs_in["duracion_yr"].mean()) if not civs_in.empty else 0.0,
        "duracion_media_fuera": float(civs_out["duracion_yr"].mean()) if not civs_out.empty else 0.0,
    }

    # gráfico doble
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    sns.kdeplot(df["distancia_centro_2d"], fill=True, ax=ax1, color="blue", alpha=0.6)
    ax1.axvspan(p.ghz_inner_radius, p.ghz_outer_radius, color="gold", alpha=0.25, label="GHZ")
    ax1.set_title("Densidad por distancia al centro galáctico")
    ax1.set_xlabel("Distancia al centro (ly)")
    ax1.set_ylabel("Densidad")
    ax1.legend()
    ax1.grid(alpha=0.3)

    dur_data = [civs_in["duracion_yr"], civs_out["duracion_yr"]]
    labels = [f"GHZ (n={len(civs_in)})", f"Fuera (n={len(civs_out)})"]
    b = ax2.boxplot(dur_data, labels=labels, patch_artist=True)
    for patch, col in zip(b["boxes"], ["lightgreen", "lightcoral"]):
        patch.set_facecolor(col)
    ax2.set_title("Duración por pertenencia a GHZ")
    ax2.set_ylabel("Duración (años)")
    ax2.grid(alpha=0.3)

    out_png = out_dir / "analisis_ghz.png"
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    save_txt(out_dir / "resumen_ghz.txt", "\n".join([f"{k}: {v}" for k, v in stats.items()]))
    return out_png, stats
