# -*- coding: utf-8 -*-
"""
Paquete de simulación científica de la hipótesis del Bosque Oscuro.

Este paquete organiza la simulación en módulos autocontenidos:
- common: configuración, E/S y tipos
- sim:   generación del universo, dinámica (Paso 5), validaciones, sensibilidad y pipeline
- cli:   punto de entrada por línea de comandos
"""
__all__ = ["common", "sim", "cli"]
__version__ = "0.1.0"
