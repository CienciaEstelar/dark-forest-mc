# -*- coding: utf-8 -*-
"""
MÓDULO: run_pipeline
====================

Propósito
---------
Este script actúa como **orquestador** del proyecto “Bosque Oscuro”.
Su tarea es ejecutar **en un solo comando**:

1. La simulación científica principal
   (`bosque_oscuro.cli.sim_main`)
2. El análisis/post-procesamiento de resultados
   (`bosque_oscuro.cli.analyze_main`)
3. (Opcional) Un **resumen narrativo generado por un LLM** a partir
   de las métricas del análisis (`--llm-narrative`)

Con esto el usuario no tiene que lanzar dos o tres comandos separados
ni acordarse del orden exacto de ejecución.

Contexto de los otros módulos
-----------------------------
- `bosque_oscuro.cli.sim_main`
    - Genera catálogos CSV (pesimista y, opcionalmente, optimista)
    - Genera mapas estáticos
    - Puede generar PDF de simulación
    - Usa:
        - `sim/espacio.py` → distribución espacial
        - `sim/tiempos.py` → nacimiento/muerte/coexistencia
        - `sim/dinamica.py` → paso 5 (Bosque Oscuro)
        - `sim/sociologia.py` → reglas de ataque
        - `common/config.py` → parámetros globales
        - `common/io_utils.py` → logs / estructura de carpetas

- `bosque_oscuro.cli.analyze_main`
    - Consume lo que dejó la simulación
    - Calcula:
        - vecino más cercano
        - % en GHZ
        - destrucciones/activas
        - (opcional) robustez
    - Puede generar un PDF de análisis

- `bosque_oscuro.analysis.narrativa_llm`
    - (nuevo) Toma un JSON de métricas (por ej. `metrics_final.json`)
      y construye un **prompt controlado** para una LLM (Gemini u OpenAI)
      para producir una narrativa rica, honesta y con secciones fijas.

Uso
---
Ejecutar SIEMPRE desde el directorio **padre** del paquete `bosque_oscuro/`.
Ejemplo con la estructura actual del proyecto:

    vault-juan/proyectos/
    └── bosque_oscuro/
        ├── __init__.py
        ├── cli/
        ├── sim/
        ├── analysis/
        ├── common/
        └── scripts/
            └── run_pipeline.py   ← este archivo

entonces:

    cd vault-juan/proyectos
    python -m bosque_oscuro.scripts.run_pipeline \
        --outdir ./output_sim \
        --dpi 600 \
        --seed 42 \
        --no-animation \
        --no-sensitivity \
        --analysis-outdir ./output_analisis \
        --analysis-generate-pdf \
        --llm-narrative \
        --llm-provider gemini \
        --llm-model gemini-2.5-pro

Notas importantes
-----------------
- Si la **simulación** falla → el **análisis no** se ejecuta.
- Si el **análisis** no se ejecuta → la **narrativa LLM** no se intenta.
- La narrativa busca un archivo de métricas dentro de `--analysis-outdir`
  con estos nombres, en este orden:
    1. `metrics_final.json`
    2. `resumen_analisis.json`
    3. `analisis.json`
  Si no encuentra ninguno, le pasa un dict vacío a la LLM y el prompt dirá
  que los datos son limitados.
- El parámetro `--llm-output` te deja elegir dónde guardar el `.md`,
  si no lo das, lo guarda en el mismo `--analysis-outdir`.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import os
import json
from typing import List, Optional


# Intentamos importar la narrativa LLM; si no está, lo dejamos opcional
try:
    from bosque_oscuro.analysis.narrativa_llm import generate_narrative
    _HAS_LLM = True
except Exception:
    _HAS_LLM = False


# ---------------------------------------------------------------------------
# Helpers de ejecución
# ---------------------------------------------------------------------------
def run_cmd(cmd: List[str]) -> int:
    """
    Ejecuta un comando en un subproceso y muestra la salida en tiempo real.

    Parameters
    ----------
    cmd : list[str]
        Comando completo a ejecutar, ya tokenizado. Ej.:
        ['python', '-m', 'bosque_oscuro.cli.sim_main', '--outdir', '...']

    Returns
    -------
    int
        Código de salida del proceso hijo. 0 = OK, != 0 = error.
    """
    print("\n" + "═" * 72)
    print(f"▶ Ejecutando comando: {' '.join(cmd)}")
    print("═" * 72)

    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    proc.communicate()

    return proc.returncode


# ---------------------------------------------------------------------------
# Construcción de comandos
# ---------------------------------------------------------------------------
def build_sim_command(args: argparse.Namespace) -> List[str]:
    """
    Construye el comando que invoca a la simulación principal
    (`bosque_oscuro.cli.sim_main`) en base a los argumentos CLI.
    """
    cmd = [
        sys.executable,
        "-m",
        "bosque_oscuro.cli.sim_main",
        "--outdir",
        args.outdir,
        "--dpi",
        str(args.dpi),
    ]

    if args.seed is not None:
        cmd += ["--seed", str(args.seed)]

    if args.full_optimistic:
        cmd.append("--full-optimistic")

    if args.enable_ftl:
        cmd.append("--enable-ftl")

    if args.generate_report:
        cmd.append("--generate-report")

    if args.no_animation:
        cmd.append("--no-animation")

    if args.no_sensitivity:
        cmd.append("--no-sensitivity")

    return cmd


def build_analysis_command(args: argparse.Namespace) -> List[str]:
    """
    Construye el comando que invoca al análisis avanzado
    (`bosque_oscuro.cli.analyze_main`).
    """
    cmd = [
        sys.executable,
        "-m",
        "bosque_oscuro.cli.analyze_main",
        "--sim-dir",
        args.outdir,
        "--outdir",
        args.analysis_outdir,
    ]

    if args.analysis_generate_pdf:
        cmd.append("--generate-pdf")

    return cmd


# ---------------------------------------------------------------------------
# Lector de métricas para el LLM
# ---------------------------------------------------------------------------
def load_analysis_metrics(analysis_outdir: str) -> dict:
    """
    Busca un JSON de métricas en el directorio de análisis.

    Orden de búsqueda:
    1. metrics_final.json
    2. resumen_analisis.json
    3. analisis.json

    Si no encuentra ninguno, devuelve {}.
    """
    candidates = [
        os.path.join(analysis_outdir, "metrics_final.json"),
        os.path.join(analysis_outdir, "resumen_analisis.json"),
        os.path.join(analysis_outdir, "analisis.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ No se pudo leer {path}: {e}")
    return {}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    """
    Define y parsea los argumentos de línea de comandos del orquestador.
    """
    parser = argparse.ArgumentParser(
        description="Pipeline completo: simulación del Bosque Oscuro + análisis + (opcional) narrativa LLM.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # -----------------------------
    # PARÁMETROS PARA LA SIMULACIÓN
    # -----------------------------
    parser.add_argument(
        "--outdir",
        type=str,
        default="replica_cientifica",
        help="Directorio donde la simulación guardará catálogos, mapas y logs.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Semilla para reproducibilidad.",
    )
    parser.add_argument(
        "--full-optimistic",
        action="store_true",
        help="Ejecuta también el escenario optimista (cuidado: muy pesado).",
    )
    parser.add_argument(
        "--enable-ftl",
        action="store_true",
        help="Activa FTL en la dinámica del paso 5.",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Pide al simulador que genere el PDF científico.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolución (dpi) para las visualizaciones.",
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Desactiva animaciones en la simulación.",
    )
    parser.add_argument(
        "--no-sensitivity",
        action="store_true",
        help="Desactiva análisis de sensibilidad (SALib) en la simulación.",
    )

    # ---------------------------
    # PARÁMETROS PARA EL ANÁLISIS
    # ---------------------------
    parser.add_argument(
        "--analysis-outdir",
        type=str,
        default="analisis_replica",
        help="Directorio donde el análisis dejará gráficos, JSON y PDF.",
    )
    parser.add_argument(
        "--analysis-generate-pdf",
        action="store_true",
        help="Genera también el PDF del análisis.",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Ejecuta solo la simulación y NO el análisis.",
    )

    # ----------------------------------------
    # PARÁMETROS PARA LA NARRATIVA CON LLM
    # ----------------------------------------
    parser.add_argument(
        "--llm-narrative",
        action="store_true",
        help="Tras el análisis, genera narrativa con LLM.",
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        default="gemini",
        choices=["gemini", "openai", "none"],
        help="Proveedor LLM a usar.",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gemini-1.5-pro",
        help="Nombre del modelo en el proveedor.",
    )
    parser.add_argument(
        "--llm-output",
        type=str,
        default=None,
        help="Ruta de salida del .md con la narrativa. Si no se define, va a --analysis-outdir.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Orquesta todo el pipeline.

    Flujo:
    1. Simulación
    2. (opcional) Análisis
    3. (opcional) Narrativa LLM
    """
    args = parse_args()

    print("\n🚀 PIPELINE ‘BOSQUE OSCURO’ — INICIO")
    print("   (simulación → análisis → narrativa LLM opcional)\n")

    # 1) SIMULACIÓN
    sim_cmd = build_sim_command(args)
    sim_exit = run_cmd(sim_cmd)
    if sim_exit != 0:
        print("\n❌ La simulación NO terminó correctamente. Código:", sim_exit)
        print("   Se aborta el pipeline y NO se ejecuta el análisis ni la narrativa.")
        sys.exit(sim_exit)

    print("\n✅ Simulación completada correctamente.")

    # 2) ¿hay que saltar el análisis?
    if args.skip_analysis:
        print("\nℹ Se pidió --skip-analysis, por lo que el pipeline termina aquí.")
        if args.llm_narrative:
            print("⚠️ Se pidió --llm-narrative pero no hay análisis. No se genera narrativa.")
        print("✅ PIPELINE COMPLETO (solo simulación).")
        sys.exit(0)

    # 3) ANÁLISIS
    analysis_cmd = build_analysis_command(args)
    analysis_exit = run_cmd(analysis_cmd)
    if analysis_exit != 0:
        print("\n❌ El análisis NO terminó correctamente. Código:", analysis_exit)
        sys.exit(analysis_exit)

    print("\n✅ Análisis completado correctamente.")

    # 4) NARRATIVA LLM (opcional)
    if args.llm_narrative:
        if not _HAS_LLM:
            print("⚠️ Se pidió --llm-narrative pero el módulo bosque_oscuro.analysis.narrativa_llm no está disponible.")
            print("   Revisa que exista el archivo y que tengas las dependencias (google-genai, python-dotenv, etc.).")
            sys.exit(0)

        print("\n🧠 Generando narrativa con LLM…")

        # cargamos métricas del análisis
        metrics = load_analysis_metrics(args.analysis_outdir)
        if not metrics:
            print("⚠️ No se encontró ningún JSON de métricas en el análisis. La narrativa será limitada.")

        # ruta de salida
        if args.llm_output:
            out_md = args.llm_output
        else:
            out_md = os.path.join(args.analysis_outdir, "informe_narrativo_llm.md")

        try:
            generate_narrative(
                metrics=metrics,
                provider=args.llm_provider,
                model=args.llm_model,
                outfile=out_md,
                sim_dir=args.outdir,
                analysis_dir=args.analysis_outdir,
            )
            print(f"✅ Narrativa LLM generada en: {out_md}")
        except Exception as e:
            print(f"⚠️ No se pudo generar narrativa LLM: {e}")

    print("\n🎉 PIPELINE ‘BOSQUE OSCURO’ — FINALIZADO CON ÉXITO ✅")


if __name__ == "__main__":
    main()
