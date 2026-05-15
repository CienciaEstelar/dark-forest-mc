"""
Módulos de análisis post-simulación del proyecto Bosque Oscuro.

Incluye:
- carga de catálogos
- análisis espacial (vecino más cercano, GHZ)
- análisis de destrucciones (Paso 5)
- validación de robustez sobre múltiples ejecuciones
- generación de reporte PDF (si reportlab está disponible)
"""
__all__ = [
    "loader",
    "vecino",
    "ghz",
    "destruccion",
    "robustez",
    "visualizacion",
    "report_pdf",
]
