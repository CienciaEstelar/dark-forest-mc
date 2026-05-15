"""
CLI de la simulación modular del Bosque Oscuro.

Ejemplo:
python -m bosque_oscuro.cli.sim_main \
  --outdir replica_cientifica --seed 42 --full-optimistic --enable-ftl \
  --dpi 600 --no-animation --sensitivity --generate-report
"""

import argparse
import json
from ..sim.pipeline import run_full_pipeline

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Simulación Científica del Bosque Oscuro (paquete modular)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    p.add_argument("--outdir", type=str, default="bosque_oscuro_output", help="Directorio de salida")
    p.add_argument("--seed", type=int, default=None, help="Semilla RAND para reproducibilidad")
    p.add_argument("--dpi", type=int, default=300, help="DPI para imágenes")
    p.add_argument("--full-optimistic", action="store_true", help="Ejecuta también el escenario optimista (cap por ENV OPTIMISTIC_CAP)")
    p.add_argument("--enable-ftl", action="store_true", help="Activa dinámica FTL en Paso 5")
    # Flags informativos (no implementamos animación aquí para mantener core limpio)
    anim = p.add_mutually_exclusive_group()
    anim.add_argument("--animation", action="store_true", default=False, help="(No-op aquí) Reservado para futuras animaciones")
    anim.add_argument("--no-animation", action="store_true", default=True, help="Desactiva animaciones")

    sens = p.add_mutually_exclusive_group()
    sens.add_argument("--sensitivity", action="store_true", default=False, help="Ejecuta sensibilidad Sobol si SALib está instalado")
    sens.add_argument("--no-sensitivity", action="store_true", default=False, help="No ejecutar sensibilidad")

    p.add_argument("--generate-report", action="store_true", help="Genera resumen JSON con métricas clave")
    return p

def main():
    parser = build_parser()
    args = parser.parse_args()

    result = run_full_pipeline(
        outdir=args.outdir,
        seed=args.seed,
        full_optimistic=bool(args.full_optimistic),
        enable_ftl=bool(args.enable_ftl),
        dpi=int(args.dpi),
        do_sensitivity=bool(args.sensitivity and not args.no_sensitivity),
        generate_report=bool(args.generate_report)
    )
    # Salida mínima legible + JSON para automatizar
    print("\n=== RESUMEN EJECUCIÓN ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
