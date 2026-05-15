# Dark Forest Monte Carlo

Simulación Monte Carlo del ciclo completo **detección → destrucción → silencio** de la hipótesis del Bosque Oscuro (solución a la Paradoja de Fermi).

Target de publicación: International Journal of Astrobiology.

Ver `CLAUDE.md` para documentación completa del proyecto, parámetros y estado.

---

## Entorno de ejecución requerido

El pipeline requiere Anaconda Python con numpy, scipy, pandas y SALib instalados. El Python del sistema (`/usr/bin/python3`) no tiene estas dependencias.

Activar antes de cualquier comando:

```bash
source ~/anaconda3/bin/activate
```

Luego ejecutar normalmente:

```bash
python -m bosque_oscuro.run_pipeline ...
```
