"""
Visualizaciones específicas del análisis (3D estático y mapa 2D).
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def visualizar_3d(df: pd.DataFrame, out_dir: str | Path, dpi: int = 600) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")

    sc = ax.scatter(
        df["posicion_x_ly"],
        df["posicion_y_ly"],
        df["posicion_z_ly"],
        c=df["tiempo_nacimiento_yr"],
        cmap="viridis",
        s=15,
        alpha=0.8,
    )
    ax.set_xlabel("X (ly)")
    ax.set_ylabel("Y (ly)")
    ax.set_zlabel("Z (ly)")
    ax.set_title("Distribución 3D de civilizaciones")
    cbar = plt.colorbar(sc, ax=ax, shrink=0.6)
    cbar.set_label("Tiempo de nacimiento (años)")

    out_png = out_dir / "visualizacion_3d.png"
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_png
