"""
CLI de análisis post-simulación.

Ejemplos:

1) Analizar una sola simulación:
python -m bosque_oscuro.cli.analyze_main --sim-dir bosque_oscuro_output --generate-pdf

2) Analizar varias simulaciones (robustez):
python -m bosque_oscuro.cli.analyze_main --multi-dirs sim1 sim2 sim3 --generate-pdf
"""

import argparse
from pathlib import Path
import json

from ..analysis.loader import cargar_catalogos
from ..analysis.vecino import analizar_vecino_mas_cercano
from ..analysis.ghz import analizar_ghz
from ..analysis.destruccion import analizar_destrucciones
from ..analysis.robustez import analizar_robustez
from ..analysis.visualizacion import visualizar_3d
from ..analysis.report_pdf import generar_pdf_sintesis
from ..common.config import Parametros

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Análisis avanzado de resultados del Bosque Oscuro",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--sim-dir", type=str, help="Directorio de UNA simulación")
    g.add_argument("--multi-dirs", nargs="+", help="Lista de directorios de simulaciones (para robustez)")
    p.add_argument("--outdir", type=str, default="analisis_avanzado", help="Directorio donde dejar las figuras/reportes")
    p.add_argument("--dpi", type=int, default=600, help="Resolución de imágenes")
    p.add_argument("--generate-pdf", action="store_true", help="Generar reporte PDF si hay reportlab")
    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    stats_global = {}
    images_global = {}
    pconf = Parametros()

    if args.sim_dir:
        # ---- análisis de una simulación ----
        cats = cargar_catalogos(args.sim_dir)
        df = cats["civs_pesimista"]
        df_p5 = cats["civs_pesimista_p5"]

        # vecino: solo civilizaciones activas supervivientes post-paso5 (FIX 1.5)
        activas = df_p5[df_p5["estado"] == "activa"].copy() if not df_p5.empty else df
        img_vecino, st_vecino = analizar_vecino_mas_cercano(activas, outdir, dpi=args.dpi, p=pconf)
        stats_global["vecino"] = st_vecino
        if img_vecino:
            images_global["vecino"] = img_vecino

        # ghz (sobre catálogo inicial — distribución de nacimientos)
        img_ghz, st_ghz = analizar_ghz(df, pconf, outdir, dpi=args.dpi)
        stats_global["ghz"] = st_ghz
        images_global["ghz"] = img_ghz

        # destrucciones
        img_dest, st_dest = analizar_destrucciones(df_p5 if not df_p5.empty else df, outdir, dpi=args.dpi)
        stats_global["destrucciones"] = st_dest
        if img_dest:
            images_global["destrucciones"] = img_dest

        # 3D
        img_3d = visualizar_3d(df, outdir, dpi=args.dpi)
        images_global["visualizacion_3d"] = img_3d

        if args.generate_pdf:
            pdf_path = generar_pdf_sintesis(outdir, stats_global, images_global)
            if pdf_path:
                print(f"✅ PDF generado: {pdf_path}")

    else:
        # ---- análisis de robustez sobre varias simulaciones ----
        stats_rob = analizar_robustez(args.multi_dirs)
        stats_global["robustez"] = stats_rob

        # guardar JSON
        with open(outdir / "robustez.json", "w", encoding="utf-8") as f:
            json.dump(stats_rob, f, indent=2, ensure_ascii=False)

        if args.generate_pdf:
            # reporte simple con solo robustez
            pdf_path = generar_pdf_sintesis(outdir, {"vecino": {}, "ghz": {}, "destrucciones": {}}, {})
            if pdf_path:
                print(f"✅ PDF generado (robustez): {pdf_path}")

    # dump resumen
    with open(outdir / "resumen_analisis.json", "w", encoding="utf-8") as f:
        json.dump(stats_global, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
