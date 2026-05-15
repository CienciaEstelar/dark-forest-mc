"""
Reporte PDF científico (opcional) para el análisis.

Si reportlab no está instalado, este módulo puede no usarse desde el CLI.
"""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

def generar_pdf_sintesis(out_dir: str | Path,
                         stats: Dict[str, Dict],
                         images: Dict[str, Path],
                         nombre: str = "Reporte_Analisis_Bosque_Oscuro.pdf") -> Optional[Path]:
    if not REPORTLAB_OK:
        return None

    out_dir = Path(out_dir)
    pdf_path = out_dir / nombre
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Análisis Científico — Proyecto Bosque Oscuro", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # 1. Vecino más cercano
    if "vecino" in stats and stats["vecino"]:
        story.append(Paragraph("1. Aislamiento (Vecino más cercano)", styles["Heading2"]))
        data = [["Métrica", "Valor"]]
        for k, v in stats["vecino"].items():
            data.append([k, f"{v:,.2f}" if isinstance(v, float) else str(v)])
        t = Table(data, colWidths=[2.5 * inch, 3.0 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        if images.get("vecino"):
            story.append(RLImage(str(images["vecino"]), width=6 * inch, height=4 * inch))

    # 2. GHZ
    if "ghz" in stats and stats["ghz"]:
        story.append(PageBreak())
        story.append(Paragraph("2. Zona Galáctica Habitable (GHZ)", styles["Heading2"]))
        data = [
            ["Métrica", "Valor"],
            ["% en GHZ", f"{stats['ghz'].get('porcentaje_en_ghz', 0):.2f}%"],
            ["Civs en GHZ", f"{stats['ghz'].get('civs_en_ghz', 0):,}"],
            ["Civs fuera GHZ", f"{stats['ghz'].get('civs_fuera_ghz', 0):,}"],
        ]
        t = Table(data, colWidths=[3.0 * inch, 2.5 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        if images.get("ghz"):
            story.append(RLImage(str(images["ghz"]), width=6 * inch, height=4 * inch))

    # 3. Destrucciones
    if "destrucciones" in stats and stats["destrucciones"]:
        story.append(PageBreak())
        story.append(Paragraph("3. Dinámica del Bosque Oscuro (destrucciones)", styles["Heading2"]))
        data = [
            ["Total civs", f"{stats['destrucciones'].get('total', 0):,}"],
            ["Destruidas", f"{stats['destrucciones'].get('destruidas', 0):,}"],
            ["Activas", f"{stats['destrucciones'].get('activas', 0):,}"],
            ["Tasa destrucción", f"{stats['destrucciones'].get('tasa_destruccion_pct', 0):.2f}%"],
        ]
        t = Table(data, colWidths=[3.0 * inch, 2.5 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        if images.get("destrucciones"):
            story.append(RLImage(str(images["destrucciones"]), width=6 * inch, height=4 * inch))

    doc.build(story)
    return pdf_path
